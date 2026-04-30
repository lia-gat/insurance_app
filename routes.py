from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Client, Policy, Payment, Claim, PolicyHistory, MortalityRate, MortalityTable, Reserve
from datetime import datetime, date
import math

main       = Blueprint('main',    __name__)
client_bp  = Blueprint('clients', __name__)
policy_bp  = Blueprint('policy',  __name__)
payment_bp = Blueprint('payment', __name__)
claim_bp   = Blueprint('claim',   __name__)


# ---------------------------------------------------------------------------
# Вспомогательная функция: парсинг даты из формы
# ---------------------------------------------------------------------------
def parse_date(value):
    """Преобразует строку 'YYYY-MM-DD' в объект date. Возвращает None если пусто."""
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%d').date()


# ---------------------------------------------------------------------------
# Вспомогательная функция: получение qx из таблицы смертности
# ---------------------------------------------------------------------------
def get_mortality_rate(age, gender):
    """Возвращает qx из последней загруженной таблицы смертности для заданного возраста и пола."""
    table = MortalityTable.query.filter_by(gender=gender).order_by(MortalityTable.year.desc()).first()
    if table:
        rate = MortalityRate.query.filter_by(table_id=table.id, age=age).first()
        if rate:
            return rate.qx
    # fallback: упрощённая линейная аппроксимация
    return max(0.001, age * 0.0005)


# ===========================================================================
# 1. ГЛАВНАЯ СТРАНИЦА
# ===========================================================================
@main.route('/')
def index():
    # --- сводные показатели портфеля ---
    total_clients   = Client.query.count()
    total_policies  = Policy.query.count()
    active_policies = Policy.query.filter_by(status='active').count()

    all_payments = Payment.query.all()
    all_policies = Policy.query.all()
    all_claims   = Claim.query.all()

    # Просроченные платежи: payments с датой в прошлом и статусом не confirmed
    overdue_payments = Payment.query.filter(
        Payment.payment_date < date.today(),
        Payment.status != 'confirmed'
    ).count()

    # Общая страховая сумма портфеля
    total_portfolio = sum(p.sum_insured or 0 for p in all_policies)

    # Ожидаемая прибыль: все взносы минус все выплаты
    total_premiums = sum(p.amount for p in all_payments if p.payment_type == 'premium')
    total_paid_out = sum(c.approved_amount or 0 for c in all_claims)
    expected_profit = total_premiums - total_paid_out

    # --- аналитика для графиков (передаём в шаблон как JSON-ready списки) ---

    # Возрастное распределение клиентов (бакеты по 10 лет)
    clients_all = Client.query.all()
    age_buckets = {}
    for c in clients_all:
        bucket = (c.age // 10) * 10
        label  = f"{bucket}–{bucket+9}"
        age_buckets[label] = age_buckets.get(label, 0) + 1
    age_labels  = sorted(age_buckets.keys())
    age_values  = [age_buckets[l] for l in age_labels]

    # Динамика резерва: суммируем Reserve.reserve_amount по дате
    reserves = Reserve.query.order_by(Reserve.date).all()
    reserve_dates  = [str(r.date)           for r in reserves]
    reserve_values = [float(r.reserve_amount) for r in reserves]

    # График платёжного расписания: суммы платежей по месяцам
    payment_by_month = {}
    for p in all_payments:
        key = p.payment_date.strftime('%Y-%m')
        payment_by_month[key] = payment_by_month.get(key, 0) + float(p.amount)
    pay_labels = sorted(payment_by_month.keys())[-12:]   # последние 12 месяцев
    pay_values = [round(payment_by_month[k], 2) for k in pay_labels]

    # qx из таблицы (пример: мужчины, возраст 30-70)
    mort_ages   = list(range(30, 75, 5))
    mort_male   = [round(get_mortality_rate(a, 'M') * 1000, 3) for a in mort_ages]   # ‰
    mort_female = [round(get_mortality_rate(a, 'F') * 1000, 3) for a in mort_ages]

    return render_template(
        'index.html',
        total_clients=total_clients,
        total_policies=total_policies,
        active_policies=active_policies,
        overdue_payments=overdue_payments,
        total_portfolio=round(total_portfolio, 2),
        expected_profit=round(expected_profit, 2),
        age_labels=age_labels,
        age_values=age_values,
        reserve_dates=reserve_dates,
        reserve_values=reserve_values,
        pay_labels=pay_labels,
        pay_values=pay_values,
        mort_ages=mort_ages,
        mort_male=mort_male,
        mort_female=mort_female,
    )


# ===========================================================================
# 2. СПИСОК КЛИЕНТОВ
# ===========================================================================
@client_bp.route('/clients', methods=['GET'])
def clients():
    name   = request.args.get('name',   '').strip()
    status = request.args.get('status', '')
    gender = request.args.get('gender', '')
    age    = request.args.get('age',    '').strip()

    query = Client.query

    if name:
        query = query.filter(Client.full_name.ilike(f'%{name}%'))
    if status:
        query = query.filter(Client.status == status)
    if gender:
        query = query.filter(Client.gender == gender)

    all_clients = query.all()

    # Фильтр по возрасту — вычисляемое поле, делаем в Python
    if age:
        try:
            age_int = int(age)
            all_clients = [c for c in all_clients if c.age == age_int]
        except ValueError:
            pass

    return render_template('clients.html', clients=all_clients)


# ===========================================================================
# 3. СТРАНИЦА КЛИЕНТА
# ===========================================================================
@client_bp.route('/client/<int:id>')
def client_detail(id):
    client = Client.query.get_or_404(id)

    payments = []
    claims   = []
    for p in client.policies:
        payments.extend(p.payments)
        claims.extend(p.claims)

    # Сортируем по дате (новые сверху)
    payments.sort(key=lambda x: x.payment_date, reverse=True)
    claims.sort(key=lambda x: x.claim_date or date.min, reverse=True)

    # История изменений клиента берётся из PolicyHistory всех его договоров
    history = []
    for p in client.policies:
        history.extend(p.history)
    history.sort(key=lambda x: x.change_date or date.min, reverse=True)

    # Риск-скор: используем qx из таблицы смертности + нагрузка по договорам
    qx         = get_mortality_rate(client.age, client.gender or 'M')
    policy_load = len(client.policies) * 0.05
    risk_score  = round(qx + policy_load, 4)

    return render_template(
        'client_detail.html',
        client=client,
        payments=payments,
        claims=claims,
        history=history,
        risk_score=risk_score,
    )


# ===========================================================================
# СОЗДАНИЕ КЛИЕНТА
# ===========================================================================
@client_bp.route('/add_client', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        client = Client(
            full_name  = request.form['full_name'].strip(),
            birth_date = parse_date(request.form['birth_date']),
            gender     = request.form['gender'],
            phone      = request.form.get('phone', '').strip() or None,
            email      = request.form.get('email', '').strip() or None,
            address    = request.form.get('address', '').strip() or None,
            status     = request.form.get('status', 'alive'),
        )
        if client.status == 'deceased':
            client.death_date = parse_date(request.form.get('death_date'))

        db.session.add(client)
        db.session.commit()
        flash('Клиент успешно создан', 'success')
        return redirect(url_for('clients.clients'))

    return render_template('add_client.html')


# ===========================================================================
# РЕДАКТИРОВАНИЕ КЛИЕНТА
# ===========================================================================
@client_bp.route('/edit_client/<int:id>', methods=['GET', 'POST'])
def edit_client(id):
    client = Client.query.get_or_404(id)

    if request.method == 'POST':
        client.full_name  = request.form['full_name'].strip()
        client.birth_date = parse_date(request.form['birth_date'])
        client.gender     = request.form['gender']
        client.phone      = request.form.get('phone', '').strip() or None
        client.email      = request.form.get('email', '').strip() or None
        client.address    = request.form.get('address', '').strip() or None
        client.status     = request.form['status']

        if client.status == 'deceased':
            client.death_date = parse_date(request.form.get('death_date'))
        else:
            client.death_date = None

        db.session.commit()
        flash('Данные клиента обновлены', 'success')
        return redirect(url_for('clients.client_detail', id=id))

    return render_template('edit_client.html', client=client)


# ===========================================================================
# УДАЛЕНИЕ КЛИЕНТА (POST — защита от случайного удаления)
# ===========================================================================
@client_bp.route('/delete_client/<int:id>', methods=['POST'])
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Клиент удалён', 'info')
    return redirect(url_for('clients.clients'))


# ===========================================================================
# 4. СПИСОК ДОГОВОРОВ
# ===========================================================================
@policy_bp.route('/policies')
def policies():
    contract_number = request.args.get('contract_number', '').strip()
    status          = request.args.get('status', '')
    insurance_type  = request.args.get('insurance_type', '')
    client_name     = request.args.get('client_name', '').strip()

    query = Policy.query

    if contract_number:
        query = query.filter(Policy.contract_number.ilike(f'%{contract_number}%'))
    if status:
        query = query.filter(Policy.status == status)
    if insurance_type:
        query = query.filter(Policy.insurance_type.ilike(f'%{insurance_type}%'))
    if client_name:
        query = query.join(Client).filter(Client.full_name.ilike(f'%{client_name}%'))

    all_policies = query.all()

    return render_template('policies.html', policies=all_policies)


# ===========================================================================
# 5. СТРАНИЦА ДОГОВОРА
# ===========================================================================
@policy_bp.route('/policy/<int:id>')
def policy_detail(id):
    policy  = Policy.query.get_or_404(id)
    payments = sorted(policy.payments, key=lambda x: x.payment_date, reverse=True)
    claims   = sorted(policy.claims,   key=lambda x: x.claim_date or date.min, reverse=True)
    history  = sorted(policy.history,  key=lambda x: x.change_date or date.min, reverse=True)

    total_paid   = sum(p.amount           for p in payments)
    total_claims = sum(c.approved_amount or 0 for c in claims)

    # Резерв = страховая сумма - оплаченные взносы + выплаты
    reserve = max((policy.sum_insured or 0) - total_paid + total_claims, 0)

    # График платёжного расписания (ожидаемые взносы на весь срок)
    schedule = []
    if policy.issue_date and policy.term_years and policy.premium:
        freq = 12 if policy.premium_frequency == 'monthly' else 1
        for year in range(policy.term_years):
            for month_offset in range(freq):
                pay_month = policy.issue_date.month + month_offset
                pay_year  = policy.issue_date.year + year + (pay_month - 1) // 12
                pay_month = ((pay_month - 1) % 12) + 1
                schedule.append({
                    'date':   f"{pay_year}-{pay_month:02d}",
                    'amount': float(policy.premium),
                })

    # Данные для графика накопления резерва по договору
    reserve_rows = Reserve.query.filter_by(policy_id=id).order_by(Reserve.date).all()
    res_dates  = [str(r.date)            for r in reserve_rows]
    res_values = [float(r.reserve_amount) for r in reserve_rows]

    return render_template(
        'policy_detail.html',
        policy=policy,
        payments=payments,
        claims=claims,
        history=history,
        total_paid=round(total_paid, 2),
        total_claims=round(total_claims, 2),
        reserve=round(reserve, 2),
        schedule=schedule,
        res_dates=res_dates,
        res_values=res_values,
    )


# ===========================================================================
# СОЗДАНИЕ ДОГОВОРА
# ===========================================================================
@policy_bp.route('/add_policy', methods=['GET', 'POST'])
@policy_bp.route('/add_policy/<int:client_id>', methods=['GET', 'POST'])
def add_policy(client_id=None):
    clients = Client.query.order_by(Client.full_name).all()

    if request.method == 'POST':
        cid = int(request.form['client_id'])

        policy = Policy(
            client_id          = cid,
            contract_number    = request.form['contract_number'].strip(),
            issue_date         = parse_date(request.form['issue_date']),
            insurance_type     = request.form['insurance_type'].strip(),
            term_years         = int(request.form['term_years']),
            premium            = float(request.form['premium']),
            premium_frequency  = request.form.get('premium_frequency', 'monthly'),
            interest_rate      = float(request.form.get('interest_rate') or 0),
            sum_insured        = float(request.form['sum_insured']),
            beneficiary_name   = request.form.get('beneficiary_name', '').strip() or None,
            beneficiary_relation = request.form.get('beneficiary_relation', '').strip() or None,
            beneficiary_phone  = request.form.get('beneficiary_phone', '').strip() or None,
            beneficiary_email  = request.form.get('beneficiary_email', '').strip() or None,
            status             = 'active',
        )
        db.session.add(policy)
        db.session.commit()
        flash('Договор создан', 'success')
        return redirect(url_for('policy.policy_detail', id=policy.id))

    preselected_client = Client.query.get(client_id) if client_id else None
    return render_template('add_policy.html', clients=clients, preselected_client=preselected_client)


# ===========================================================================
# РЕДАКТИРОВАНИЕ ДОГОВОРА
# ===========================================================================
@policy_bp.route('/edit_policy/<int:id>', methods=['GET', 'POST'])
def edit_policy(id):
    policy = Policy.query.get_or_404(id)

    if request.method == 'POST':
        # Записываем историю изменений для каждого изменённого поля
        fields_to_track = ['insurance_type', 'term_years', 'premium', 'sum_insured',
                           'status', 'interest_rate', 'premium_frequency']
        for field in fields_to_track:
            new_val = request.form.get(field)
            old_val = str(getattr(policy, field) or '')
            if new_val and new_val != old_val:
                entry = PolicyHistory(
                    policy_id   = policy.id,
                    change_date = date.today(),
                    field_name  = field,
                    old_value   = old_val,
                    new_value   = new_val,
                    value_type  = 'str',
                )
                db.session.add(entry)

        policy.insurance_type    = request.form['insurance_type'].strip()
        policy.term_years        = int(request.form['term_years'])
        policy.premium           = float(request.form['premium'])
        policy.premium_frequency = request.form.get('premium_frequency', 'monthly')
        policy.interest_rate     = float(request.form.get('interest_rate') or 0)
        policy.sum_insured       = float(request.form['sum_insured'])
        policy.status            = request.form['status']
        policy.beneficiary_name  = request.form.get('beneficiary_name', '').strip() or None
        policy.beneficiary_relation = request.form.get('beneficiary_relation', '').strip() or None
        policy.beneficiary_phone = request.form.get('beneficiary_phone', '').strip() or None
        policy.beneficiary_email = request.form.get('beneficiary_email', '').strip() or None

        db.session.commit()
        flash('Договор обновлён', 'success')
        return redirect(url_for('policy.policy_detail', id=id))

    return render_template('edit_policy.html', policy=policy)


# ===========================================================================
# УДАЛЕНИЕ ДОГОВОРА (POST)
# ===========================================================================
@policy_bp.route('/delete_policy/<int:id>', methods=['POST'])
def delete_policy(id):
    policy = Policy.query.get_or_404(id)
    client_id = policy.client_id
    db.session.delete(policy)
    db.session.commit()
    flash('Договор удалён', 'info')
    return redirect(url_for('clients.client_detail', id=client_id))


# ===========================================================================
# 6. АКТУАРНЫЙ РАСЧЁТ
# ===========================================================================
@policy_bp.route('/calculations/<int:policy_id>', methods=['GET', 'POST'])
def calculations(policy_id):
    policy = Policy.query.get_or_404(policy_id)
    result = None

    if request.method == 'POST':
        discount_rate = float(request.form['discount_rate'])  # например 0.05
        inflation     = float(request.form['inflation'])       # например 0.03
        scenario      = request.form['scenario']

        age    = policy.client.age
        gender = policy.client.gender or 'M'

        # Базовая qx из таблицы смертности (или fallback)
        qx = get_mortality_rate(age, gender)

        # Сценарные поправки
        scenario_multipliers = {
            'pessimistic': 1.5,
            'baseline':    1.0,
            'optimistic':  0.7,
        }
        qx_scenario = qx * scenario_multipliers.get(scenario, 1.0)

        S  = float(policy.sum_insured or 0)
        n  = int(policy.term_years or 1)
        P  = float(policy.premium or 0)
        v  = 1 / (1 + discount_rate)  # дисконтный множитель

        # --- Ожидаемая приведённая стоимость выплат (EPV) ---
        # EPV = S * sum_{t=1}^{n} qx * v^t  (упрощённая модель: qx постоянна)
        epv = S * qx_scenario * sum(v**t for t in range(1, n + 1))

        # --- Аннуитет взносов ---
        annuity = sum(v**t for t in range(1, n + 1))  # a_{n|}

        # --- Нетто-премия (годовая) ---
        net_premium = epv / annuity if annuity else 0

        # --- Дисперсия (Бернулли) ---
        variance = (S ** 2) * qx_scenario * (1 - qx_scenario)
        std_dev  = math.sqrt(variance)

        # --- Нетто-резерв на конец 1-го года (prospective) ---
        # tV = EPV(будущих выплат) - EPV(будущих взносов)
        epv_future    = S * qx_scenario * sum(v**t for t in range(1, n))
        annuity_future = sum(v**t for t in range(1, n))
        reserve_1yr   = max(epv_future - net_premium * annuity_future, 0)

        # --- Ожидаемая прибыль ---
        # реальные взносы за весь срок - ожидаемые выплаты с учётом инфляции
        expected_profit = P * n - epv * (1 + inflation)

        result = {
            'net_premium':       round(net_premium,    2),
            'expected_loss':     round(epv,             2),
            'variance':          round(variance,        2),
            'std_dev':           round(std_dev,         2),
            'loss_probability':  round(qx_scenario,     4),
            'reserve':           round(reserve_1yr,     2),
            'expected_profit':   round(expected_profit, 2),
            'annuity':           round(annuity,         4),
            'discount_factor':   round(v,               4),
            'qx_used':           round(qx_scenario,     5),
            'scenario':          scenario,
        }

    return render_template('calculations.html', policy=policy, result=result)


# ===========================================================================
# 9. ПЛАТЕЖИ (все платежи системы)
# ===========================================================================
@payment_bp.route('/payments', methods=['GET'])
def payments():
    policy_id  = request.args.get('policy_id')
    pay_type   = request.args.get('payment_type', '')
    status     = request.args.get('status', '')
    overdue    = request.args.get('overdue', '')

    query = Payment.query

    if policy_id:
        query = query.filter(Payment.policy_id == int(policy_id))
    if pay_type:
        query = query.filter(Payment.payment_type == pay_type)
    if status:
        query = query.filter(Payment.status == status)
    if overdue:
        query = query.filter(
            Payment.payment_date < date.today(),
            Payment.status != 'confirmed'
        )

    all_payments = query.order_by(Payment.payment_date.desc()).all()

    total_amount = sum(p.amount for p in all_payments)

    return render_template(
        'payments.html',
        payments=all_payments,
        total_amount=round(total_amount, 2),
        today=date.today(),
    )


# СОЗДАНИЕ ПЛАТЕЖА
@payment_bp.route('/add_payment/<int:policy_id>', methods=['GET', 'POST'])
def add_payment(policy_id):
    policy = Policy.query.get_or_404(policy_id)

    if request.method == 'POST':
        payment = Payment(
            policy_id    = policy_id,
            amount       = float(request.form['amount']),
            payment_date = parse_date(request.form['payment_date']),
            payment_type = request.form.get('payment_type', 'premium'),
            status       = request.form.get('status', 'confirmed'),
        )
        db.session.add(payment)
        db.session.commit()
        flash('Платёж добавлен', 'success')
        return redirect(url_for('policy.policy_detail', id=policy_id))

    return render_template('add_payment.html', policy=policy)


# ===========================================================================
# 10. ВЫПЛАТЫ (страховые случаи — claims)
# ===========================================================================
@claim_bp.route('/claims', methods=['GET'])
def claims():
    policy_id = request.args.get('policy_id')
    reason    = request.args.get('reason', '')

    query = Claim.query

    if policy_id:
        query = query.filter(Claim.policy_id == int(policy_id))
    if reason:
        query = query.filter(Claim.reason == reason)

    all_claims = query.order_by(Claim.claim_date.desc()).all()
    total_approved = sum(c.approved_amount or 0 for c in all_claims)

    return render_template(
        'claims.html',
        claims=all_claims,
        total_approved=round(total_approved, 2),
    )


# СОЗДАНИЕ ВЫПЛАТЫ
@claim_bp.route('/add_claim/<int:policy_id>', methods=['GET', 'POST'])
def add_claim(policy_id):
    policy = Policy.query.get_or_404(policy_id)

    if request.method == 'POST':
        claim = Claim(
            policy_id       = policy_id,
            claim_date      = parse_date(request.form['claim_date']),
            claim_amount    = float(request.form['claim_amount']),
            approved_amount = float(request.form.get('approved_amount') or 0),
            reason          = request.form.get('reason', 'death'),
        )
        db.session.add(claim)
        db.session.commit()
        flash('Выплата добавлена', 'success')
        return redirect(url_for('policy.policy_detail', id=policy_id))

    return render_template('add_claim.html', policy=policy)


# ===========================================================================
# 11. СЦЕНАРНЫЙ АНАЛИЗ (портфельный — не по конкретному договору)
# ===========================================================================
@main.route('/scenario_analysis', methods=['GET', 'POST'])
def scenario_analysis():
    results = None

    if request.method == 'POST':
        discount_rate = float(request.form['discount_rate'])
        inflation     = float(request.form['inflation'])

        all_policies = Policy.query.filter_by(status='active').all()
        scenarios = ['baseline', 'optimistic', 'pessimistic']
        multipliers = {'baseline': 1.0, 'optimistic': 0.7, 'pessimistic': 1.5}

        results = {}
        for sc in scenarios:
            total_epv    = 0
            total_net_p  = 0
            total_profit = 0
            total_reserve = 0

            for policy in all_policies:
                age    = policy.client.age
                gender = policy.client.gender or 'M'
                qx     = get_mortality_rate(age, gender) * multipliers[sc]
                S      = float(policy.sum_insured or 0)
                n      = int(policy.term_years or 1)
                P      = float(policy.premium or 0)
                v      = 1 / (1 + discount_rate)

                annuity = sum(v**t for t in range(1, n + 1))
                epv     = S * qx * annuity
                net_p   = epv / annuity if annuity else 0
                profit  = P * n - epv * (1 + inflation)

                epv_f   = S * qx * sum(v**t for t in range(1, n))
                ann_f   = sum(v**t for t in range(1, n))
                reserve = max(epv_f - net_p * ann_f, 0)

                total_epv     += epv
                total_net_p   += net_p
                total_profit  += profit
                total_reserve += reserve

            results[sc] = {
                'total_epv':    round(total_epv,    2),
                'total_net_p':  round(total_net_p,  2),
                'total_profit': round(total_profit, 2),
                'total_reserve':round(total_reserve,2),
                'policy_count': len(all_policies),
            }

    return render_template('scenario_analysis.html', results=results)



# 12. РЕЗЕРВЫ

@main.route('/reserves', methods=['GET'])
def reserves():
    policy_id = request.args.get('policy_id')

    if policy_id:
        # Резервы конкретного договора
        policy = Policy.query.get_or_404(int(policy_id))
        reserve_rows = Reserve.query.filter_by(policy_id=int(policy_id)).order_by(Reserve.date).all()
        return render_template('reserves.html', reserve_rows=reserve_rows, policy=policy, all_policies=None)
    else:
        # Общий резерв компании: последнее значение по каждому договору
        all_policies = Policy.query.filter_by(status='active').all()
        summary = []
        total_reserve = 0
        for p in all_policies:
            last = Reserve.query.filter_by(policy_id=p.id).order_by(Reserve.date.desc()).first()
            amount = float(last.reserve_amount) if last else 0.0
            total_reserve += amount
            summary.append({'policy': p, 'reserve': round(amount, 2)})

        # Динамика суммарного резерва компании по месяцам
        all_res = Reserve.query.order_by(Reserve.date).all()
        dyn_by_date = {}
        for r in all_res:
            key = r.date.strftime('%Y-%m')
            dyn_by_date[key] = dyn_by_date.get(key, 0) + float(r.reserve_amount)
        dyn_labels = sorted(dyn_by_date.keys())
        dyn_values = [round(dyn_by_date[k], 2) for k in dyn_labels]

        return render_template(
            'reserves.html',
            reserve_rows=None,
            policy=None,
            all_policies=summary,
            total_reserve=round(total_reserve, 2),
            dyn_labels=dyn_labels,
            dyn_values=dyn_values,
        )