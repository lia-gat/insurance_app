"""
seed.py — Тестовые данные для системы страхования жизни.

Создаёт:
  - 10 клиентов (разный возраст, пол, статус)
  - 14 договоров (разные типы: endowment, term, life, annuity, mixed)
  - 30 платежей
  - 4 страховых выплаты (claims)
  - 6 записей резерва
  - 3 записи истории изменений договора

Подключение в app.py:
    from seed import seed_data

    def create_app():
        app = Flask(__name__)
        ...
        with app.app_context():
            db.create_all()
            _seed_mortality_table(app)
            seed_data()          # ← добавить эту строку
        return app
"""

from datetime import date, timedelta
from models import db, Client, Policy, Payment, Claim, PolicyHistory, Reserve


def seed_data():
    """Заполняет базу тестовыми данными. Повторный вызов игнорируется."""
    if Client.query.first():
        return  # данные уже есть — не перезаписываем

    # ──────────────────────────────────────────────────────────────
    # КЛИЕНТЫ
    # ──────────────────────────────────────────────────────────────
    clients = [
        Client(
            full_name  = "Иванов Алексей Дмитриевич",
            birth_date = date(1985, 3, 14),
            gender     = "M",
            phone      = "+7 (495) 111-22-33",
            email      = "ivanov.alexey@mail.ru",
            address    = "г. Москва, ул. Ленина, д. 5, кв. 12",
            status     = "alive",
        ),
        Client(
            full_name  = "Смирнова Елена Сергеевна",
            birth_date = date(1990, 7, 22),
            gender     = "F",
            phone      = "+7 (812) 222-33-44",
            email      = "smirnova.elena@gmail.com",
            address    = "г. Санкт-Петербург, пр. Невский, д. 44, кв. 3",
            status     = "alive",
        ),
        Client(
            full_name  = "Петров Николай Васильевич",
            birth_date = date(1970, 11, 5),
            gender     = "M",
            phone      = "+7 (383) 333-44-55",
            email      = "petrov.nv@yandex.ru",
            address    = "г. Новосибирск, ул. Советская, д. 18",
            status     = "alive",
        ),
        Client(
            full_name  = "Козлова Марина Андреевна",
            birth_date = date(1978, 6, 30),
            gender     = "F",
            phone      = "+7 (343) 444-55-66",
            email      = "kozlova.m@mail.ru",
            address    = "г. Екатеринбург, ул. Мира, д. 7, кв. 201",
            status     = "alive",
        ),
        Client(
            full_name  = "Новиков Сергей Игоревич",
            birth_date = date(1962, 9, 17),
            gender     = "M",
            phone      = "+7 (863) 555-66-77",
            email      = "novikov.si@inbox.ru",
            address    = "г. Ростов-на-Дону, пер. Садовый, д. 2",
            status     = "alive",
        ),
        Client(
            full_name  = "Морозова Татьяна Павловна",
            birth_date = date(1955, 1, 8),
            gender     = "F",
            phone      = "+7 (846) 666-77-88",
            email      = "morozova.tp@yandex.ru",
            address    = "г. Самара, ул. Чапаевская, д. 33, кв. 5",
            status     = "alive",
        ),
        Client(
            full_name  = "Волков Андрей Михайлович",
            birth_date = date(1993, 4, 25),
            gender     = "M",
            phone      = "+7 (351) 777-88-99",
            email      = "volkov.am@gmail.com",
            address    = "г. Челябинск, ул. Победы, д. 11",
            status     = "alive",
        ),
        Client(
            full_name  = "Соколова Ирина Владимировна",
            birth_date = date(1968, 12, 3),
            gender     = "F",
            phone      = "+7 (473) 888-99-00",
            email      = "sokolova.iv@mail.ru",
            address    = "г. Воронеж, ул. Кольцовская, д. 8, кв. 14",
            status     = "alive",
        ),
        Client(
            full_name  = "Лебедев Виктор Юрьевич",
            birth_date = date(1950, 8, 19),
            gender     = "M",
            phone      = "+7 (843) 999-00-11",
            email      = "lebedev.vy@inbox.ru",
            address    = "г. Казань, ул. Баумана, д. 17",
            status     = "deceased",
            death_date = date(2023, 5, 12),
        ),
        Client(
            full_name  = "Федорова Ольга Николаевна",
            birth_date = date(1982, 2, 11),
            gender     = "F",
            phone      = "+7 (423) 100-20-30",
            email      = "fedorova.on@yandex.ru",
            address    = "г. Владивосток, ул. Светланская, д. 25, кв. 7",
            status     = "alive",
        ),
    ]

    db.session.add_all(clients)
    db.session.flush()  # получаем id до commit

    # ──────────────────────────────────────────────────────────────
    # ДОГОВОРЫ
    # ──────────────────────────────────────────────────────────────
    policies = [
        # Клиент 1 — Иванов, 2 договора
        Policy(
            client_id          = clients[0].id,
            contract_number    = "ENDOW-2018-001",
            issue_date         = date(2018, 3, 1),
            insurance_type     = "endowment",
            term_years         = 15,
            premium            = 13000.00,
            premium_frequency  = "yearly",
            interest_rate      = 5.0,
            sum_insured        = 200000.00,
            beneficiary_name   = "Иванова Светлана Александровна",
            beneficiary_relation = "spouse",
            beneficiary_phone  = "+7 (495) 111-22-34",
            beneficiary_email  = "ivanova.sa@mail.ru",
            status             = "active",
        ),
        Policy(
            client_id          = clients[0].id,
            contract_number    = "TERM-2022-001",
            issue_date         = date(2022, 6, 15),
            insurance_type     = "term",
            term_years         = 10,
            premium            = 4500.00,
            premium_frequency  = "monthly",
            interest_rate      = 0.0,
            sum_insured        = 500000.00,
            beneficiary_name   = "Иванова Светлана Александровна",
            beneficiary_relation = "spouse",
            beneficiary_phone  = "+7 (495) 111-22-34",
            status             = "active",
        ),

        # Клиент 2 — Смирнова
        Policy(
            client_id          = clients[1].id,
            contract_number    = "ENDOW-2020-002",
            issue_date         = date(2020, 1, 10),
            insurance_type     = "endowment",
            term_years         = 20,
            premium            = 9800.00,
            premium_frequency  = "yearly",
            interest_rate      = 6.0,
            sum_insured        = 300000.00,
            beneficiary_name   = "Смирнов Денис Олегович",
            beneficiary_relation = "spouse",
            status             = "active",
        ),

        # Клиент 3 — Петров
        Policy(
            client_id          = clients[2].id,
            contract_number    = "LIFE-2015-003",
            issue_date         = date(2015, 5, 20),
            insurance_type     = "life",
            term_years         = 20,
            premium            = 18000.00,
            premium_frequency  = "yearly",
            interest_rate      = 0.0,
            sum_insured        = 350000.00,
            beneficiary_name   = "Петрова Галина Федоровна",
            beneficiary_relation = "spouse",
            status             = "active",
        ),
        Policy(
            client_id          = clients[2].id,
            contract_number    = "TERM-2021-003",
            issue_date         = date(2021, 9, 1),
            insurance_type     = "term",
            term_years         = 5,
            premium            = 6200.00,
            premium_frequency  = "yearly",
            interest_rate      = 0.0,
            sum_insured        = 150000.00,
            status             = "active",
        ),

        # Клиент 4 — Козлова
        Policy(
            client_id          = clients[3].id,
            contract_number    = "MIXED-2019-004",
            issue_date         = date(2019, 4, 5),
            insurance_type     = "mixed",
            term_years         = 15,
            premium            = 11500.00,
            premium_frequency  = "yearly",
            interest_rate      = 4.5,
            sum_insured        = 250000.00,
            beneficiary_name   = "Козлов Дмитрий Артёмович",
            beneficiary_relation = "child",
            status             = "active",
        ),

        # Клиент 5 — Новиков
        Policy(
            client_id          = clients[4].id,
            contract_number    = "ENDOW-2010-005",
            issue_date         = date(2010, 7, 1),
            insurance_type     = "endowment",
            term_years         = 20,
            premium            = 22000.00,
            premium_frequency  = "yearly",
            interest_rate      = 5.5,
            sum_insured        = 400000.00,
            beneficiary_name   = "Новикова Людмила Борисовна",
            beneficiary_relation = "spouse",
            status             = "active",
        ),

        # Клиент 6 — Морозова (пожилой клиент — пенсионный аннуитет)
        Policy(
            client_id          = clients[5].id,
            contract_number    = "ANNUITY-2016-006",
            issue_date         = date(2016, 1, 15),
            insurance_type     = "annuity",
            term_years         = 20,
            premium            = 28000.00,
            premium_frequency  = "yearly",
            interest_rate      = 7.0,
            sum_insured        = 600000.00,
            status             = "active",
        ),

        # Клиент 7 — Волков (молодой, накопительное)
        Policy(
            client_id          = clients[6].id,
            contract_number    = "ENDOW-2023-007",
            issue_date         = date(2023, 2, 1),
            insurance_type     = "endowment",
            term_years         = 25,
            premium            = 7500.00,
            premium_frequency  = "monthly",
            interest_rate      = 6.5,
            sum_insured        = 1000000.00,
            beneficiary_name   = "Волкова Анастасия Игоревна",
            beneficiary_relation = "spouse",
            status             = "active",
        ),

        # Клиент 8 — Соколова
        Policy(
            client_id          = clients[7].id,
            contract_number    = "TERM-2018-008",
            issue_date         = date(2018, 10, 10),
            insurance_type     = "term",
            term_years         = 10,
            premium            = 9000.00,
            premium_frequency  = "yearly",
            interest_rate      = 0.0,
            sum_insured        = 200000.00,
            status             = "active",
        ),

        # Клиент 9 — Лебедев (умер → договор закрыт, выплата произведена)
        Policy(
            client_id          = clients[8].id,
            contract_number    = "LIFE-2005-009",
            issue_date         = date(2005, 3, 1),
            insurance_type     = "life",
            term_years         = 25,
            premium            = 15000.00,
            premium_frequency  = "yearly",
            interest_rate      = 0.0,
            sum_insured        = 300000.00,
            beneficiary_name   = "Лебедева Зинаида Павловна",
            beneficiary_relation = "spouse",
            beneficiary_phone  = "+7 (843) 999-00-12",
            status             = "closed",
        ),

        # Клиент 10 — Фёдорова, 2 договора
        Policy(
            client_id          = clients[9].id,
            contract_number    = "ENDOW-2021-010",
            issue_date         = date(2021, 8, 20),
            insurance_type     = "endowment",
            term_years         = 12,
            premium            = 10500.00,
            premium_frequency  = "yearly",
            interest_rate      = 5.0,
            sum_insured        = 180000.00,
            status             = "active",
        ),
        Policy(
            client_id          = clients[9].id,
            contract_number    = "TERM-2024-010",
            issue_date         = date(2024, 1, 1),
            insurance_type     = "term",
            term_years         = 10,
            premium            = 3800.00,
            premium_frequency  = "monthly",
            interest_rate      = 0.0,
            sum_insured        = 400000.00,
            status             = "active",
        ),
    ]

    db.session.add_all(policies)
    db.session.flush()

    # ──────────────────────────────────────────────────────────────
    # ПЛАТЕЖИ
    # ──────────────────────────────────────────────────────────────
    def make_payments(policy, years_back, amount, frequency="yearly", status="confirmed"):
        """Генерирует платежи за указанное количество периодов назад от сегодня."""
        payments = []
        today = date.today()
        if frequency == "yearly":
            for y in range(years_back, 0, -1):
                payments.append(Payment(
                    policy_id    = policy.id,
                    amount       = amount,
                    payment_date = date(today.year - y, policy.issue_date.month, policy.issue_date.day),
                    payment_type = "premium",
                    status       = status,
                ))
        else:  # monthly — последние 6 месяцев
            for m in range(6, 0, -1):
                d = today - timedelta(days=30 * m)
                payments.append(Payment(
                    policy_id    = policy.id,
                    amount       = amount,
                    payment_date = d,
                    payment_type = "premium",
                    status       = status,
                ))
        return payments

    all_payments = []
    # Иванов — ENDOW 6 лет, TERM 2 года (monthly → 6 мес)
    all_payments += make_payments(policies[0], 6, 13000.00)
    all_payments += make_payments(policies[1], 0, 4500.00, "monthly")
    # Смирнова — 4 года
    all_payments += make_payments(policies[2], 4, 9800.00)
    # Петров — LIFE 8 лет, TERM 3 года
    all_payments += make_payments(policies[3], 8, 18000.00)
    all_payments += make_payments(policies[4], 3, 6200.00)
    # Козлова — 5 лет
    all_payments += make_payments(policies[5], 5, 11500.00)
    # Новиков — 10 лет
    all_payments += make_payments(policies[6], 10, 22000.00)
    # Морозова — 7 лет
    all_payments += make_payments(policies[7], 7, 28000.00)
    # Волков — monthly 6 мес
    all_payments += make_payments(policies[8], 0, 7500.00, "monthly")
    # Соколова — 6 лет
    all_payments += make_payments(policies[9], 6, 9000.00)
    # Лебедев — 17 лет (до смерти)
    all_payments += make_payments(policies[10], 17, 15000.00)
    # Фёдорова — ENDOW 3 года, TERM monthly 6 мес
    all_payments += make_payments(policies[11], 3, 10500.00)
    all_payments += make_payments(policies[12], 0, 3800.00, "monthly")

    # Один просроченный платёж у Новикова
    all_payments.append(Payment(
        policy_id    = policies[6].id,
        amount       = 22000.00,
        payment_date = date.today() - timedelta(days=45),
        payment_type = "premium",
        status       = "overdue",
    ))

    db.session.add_all(all_payments)

    # ──────────────────────────────────────────────────────────────
    # СТРАХОВЫЕ ВЫПЛАТЫ (CLAIMS)
    # ──────────────────────────────────────────────────────────────
    claims = [
        # Лебедев — смерть, выплата наследнику
        Claim(
            policy_id       = policies[10].id,
            claim_date      = date(2023, 5, 20),
            claim_amount    = 300000.00,
            approved_amount = 300000.00,
            reason          = "death",
        ),
        # Новиков — частичное изъятие накоплений
        Claim(
            policy_id       = policies[6].id,
            claim_date      = date(2022, 8, 1),
            claim_amount    = 50000.00,
            approved_amount = 48000.00,
            reason          = "surrender",
        ),
        # Морозова — частичная выплата аннуитета
        Claim(
            policy_id       = policies[7].id,
            claim_date      = date(2023, 1, 15),
            claim_amount    = 30000.00,
            approved_amount = 30000.00,
            reason          = "maturity",
        ),
        # Петров — досрочное расторжение срочного
        Claim(
            policy_id       = policies[4].id,
            claim_date      = date(2024, 3, 10),
            claim_amount    = 18000.00,
            approved_amount = 15000.00,
            reason          = "surrender",
        ),
    ]
    db.session.add_all(claims)

    # ──────────────────────────────────────────────────────────────
    # ИСТОРИЯ ИЗМЕНЕНИЙ ДОГОВОРОВ
    # ──────────────────────────────────────────────────────────────
    history = [
        PolicyHistory(
            policy_id   = policies[0].id,
            change_date = date(2021, 3, 1),
            field_name  = "sum_insured",
            old_value   = "150000.0",
            new_value   = "200000.0",
            value_type  = "float",
        ),
        PolicyHistory(
            policy_id   = policies[6].id,
            change_date = date(2022, 5, 15),
            field_name  = "premium",
            old_value   = "22000.0",
            new_value   = "22000.0",
            value_type  = "float",
        ),
        PolicyHistory(
            policy_id   = policies[10].id,
            change_date = date(2023, 5, 20),
            field_name  = "status",
            old_value   = "active",
            new_value   = "closed",
            value_type  = "str",
        ),
    ]
    db.session.add_all(history)

    # ──────────────────────────────────────────────────────────────
    # РЕЗЕРВЫ (контрольные значения на последнюю дату расчёта)
    # ──────────────────────────────────────────────────────────────
    today = date.today()
    reserves = [
        Reserve(policy_id=policies[0].id,  date=today, reserve_amount=45200.00),
        Reserve(policy_id=policies[2].id,  date=today, reserve_amount=72800.00),
        Reserve(policy_id=policies[3].id,  date=today, reserve_amount=118500.00),
        Reserve(policy_id=policies[5].id,  date=today, reserve_amount=98700.00),
        Reserve(policy_id=policies[6].id,  date=today, reserve_amount=241000.00),
        Reserve(policy_id=policies[11].id, date=today, reserve_amount=31500.00),
    ]
    db.session.add_all(reserves)

    # ──────────────────────────────────────────────────────────────
    db.session.commit()
    print("[seed] Тестовые данные успешно загружены: "
          f"10 клиентов, {len(policies)} договоров, "
          f"{len(all_payments)} платежей, {len(claims)} выплат.")