"""
actuarial.py — Актуарные расчёты для системы долгосрочного страхования жизни.

Реализованные модели:
    - Дисконтирование и аннуитеты
    - Нетто-премия (EPV / аннуитет)
    - Нетто-резерв (проспективный метод)
    - График накопления (endowment)
    - Расчёт по типу страхования
    - Вероятность дожития / смерти из таблицы смертности
    - Ожидаемая прибыль и дисперсия
"""

import math
from typing import Optional


# ===========================================================================
# 1. БАЗОВЫЕ АКТУАРНЫЕ ФУНКЦИИ
# ===========================================================================

def discount_factor(i: float, t: int = 1) -> float:
    """
    Дисконтный множитель v^t = 1 / (1+i)^t.

    Args:
        i: годовая ставка дисконтирования (например 0.05 = 5%)
        t: количество периодов
    Returns:
        v^t
    """
    return 1 / (1 + i) ** t


def annuity_immediate(i: float, n: int) -> float:
    """
    Аннуитет-постнумерандо a_{n|} = sum_{t=1}^{n} v^t.

    Закрытая формула: a_{n|} = (1 - v^n) / i

    Args:
        i: ставка дисконтирования
        n: срок в годах
    Returns:
        значение аннуитета
    """
    if i == 0:
        return float(n)
    v = 1 / (1 + i)
    return (1 - v ** n) / i


def annuity_due(i: float, n: int) -> float:
    """
    Аннуитет-пренумерандо ä_{n|} = sum_{t=0}^{n-1} v^t = a_{n|} * (1+i).

    Args:
        i: ставка дисконтирования
        n: срок в годах
    Returns:
        значение аннуитета-пренумерандо
    """
    return annuity_immediate(i, n) * (1 + i)


def survival_probability(qx_list: list, age: int, t: int) -> float:
    """
    Вероятность дожития t_p_x — прожить ещё t лет начиная с возраста age.

    t_p_x = prod_{k=0}^{t-1} (1 - q_{x+k})

    Args:
        qx_list: список qx индексированный по возрасту (qx_list[age] = q_age)
        age: текущий возраст
        t: количество лет
    Returns:
        вероятность дожития
    """
    prob = 1.0
    for k in range(t):
        current_age = age + k
        if current_age < len(qx_list):
            prob *= (1 - qx_list[current_age])
        else:
            prob *= (1 - 0.5)   # предельное значение для очень пожилых
    return prob


def death_probability(qx_list: list, age: int, t: int) -> float:
    """
    Вероятность смерти на t-м году — t|q_x.

    t|q_x = t_p_x * q_{x+t}

    Args:
        qx_list: таблица смертности
        age: текущий возраст
        t: горизонт (лет до события)
    Returns:
        вероятность смерти на t-м году
    """
    tp = survival_probability(qx_list, age, t)
    future_age = age + t
    if future_age < len(qx_list):
        qxt = qx_list[future_age]
    else:
        qxt = 0.5
    return tp * qxt


# ===========================================================================
# 2. НЕТТО-ПРЕМИЯ
# ===========================================================================

def net_premium_term_life(
    S: float,
    i: float,
    n: int,
    qx_list: list,
    age: int,
) -> dict:
    """
    Нетто-премия для срочного страхования на случай смерти.

    EPV выплат = S * sum_{t=0}^{n-1} t|q_x * v^{t+1}
    P = EPV / a_{n|}

    Args:
        S: страховая сумма
        i: ставка дисконтирования
        n: срок договора (лет)
        qx_list: таблица смертности
        age: возраст застрахованного
    Returns:
        словарь с EPV, аннуитетом, нетто-премией
    """
    v = 1 / (1 + i)

    # EPV выплат при смерти
    epv_death = sum(
        death_probability(qx_list, age, t) * (v ** (t + 1))
        for t in range(n)
    ) * S

    ann = annuity_immediate(i, n)
    net_p = epv_death / ann if ann > 0 else 0.0

    return {
        "epv":        round(epv_death, 4),
        "annuity":    round(ann,       4),
        "net_premium": round(net_p,    4),
    }


def net_premium_endowment(
    S: float,
    i: float,
    n: int,
    qx_list: list,
    age: int,
) -> dict:
    """
    Нетто-премия для смешанного страхования (на дожитие + на смерть).

    EPV = EPV(смерть) + EPV(дожитие)
    EPV(дожитие) = S * n_p_x * v^n

    Args:
        S: страховая сумма
        i: ставка дисконтирования
        n: срок договора
        qx_list: таблица смертности
        age: возраст
    Returns:
        словарь с составляющими и нетто-премией
    """
    v = 1 / (1 + i)

    epv_death = sum(
        death_probability(qx_list, age, t) * (v ** (t + 1))
        for t in range(n)
    ) * S

    np_x = survival_probability(qx_list, age, n)
    epv_survival = S * np_x * (v ** n)

    epv_total = epv_death + epv_survival
    ann = annuity_immediate(i, n)
    net_p = epv_total / ann if ann > 0 else 0.0

    return {
        "epv_death":    round(epv_death,    4),
        "epv_survival": round(epv_survival, 4),
        "epv_total":    round(epv_total,    4),
        "annuity":      round(ann,          4),
        "net_premium":  round(net_p,        4),
        "survival_prob": round(np_x,        5),
    }


def net_premium_whole_life(
    S: float,
    i: float,
    max_age: int,
    qx_list: list,
    age: int,
) -> dict:
    """
    Нетто-премия для пожизненного страхования.

    Args:
        S: страховая сумма
        i: ставка дисконтирования
        max_age: предельный возраст таблицы
        qx_list: таблица смертности
        age: возраст застрахованного
    Returns:
        словарь с EPV и нетто-премией
    """
    n = max_age - age
    return net_premium_term_life(S, i, n, qx_list, age)


# ===========================================================================
# 3. НЕТТО-РЕЗЕРВ (проспективный метод)
# ===========================================================================

def net_reserve(
    S: float,
    i: float,
    n: int,
    qx_list: list,
    age: int,
    t: int,
    net_p: float,
    insurance_type: str = "term",
) -> float:
    """
    Проспективный нетто-резерв на момент t лет после заключения договора.

    tV = EPV(будущих выплат) - P * a_{n-t|}

    Args:
        S: страховая сумма
        i: ставка дисконтирования
        n: полный срок договора
        qx_list: таблица смертности
        age: возраст на момент заключения
        t: прошедшее время (лет)
        net_p: годовая нетто-премия
        insurance_type: 'term', 'endowment', 'whole_life'
    Returns:
        значение резерва
    """
    if t >= n:
        return 0.0

    remaining = n - t
    current_age = age + t

    if insurance_type == "endowment":
        result = net_premium_endowment(S, i, remaining, qx_list, current_age)
        epv_future = result["epv_total"]
    else:
        result = net_premium_term_life(S, i, remaining, qx_list, current_age)
        epv_future = result["epv"]

    ann_future = annuity_immediate(i, remaining)
    reserve = epv_future - net_p * ann_future

    return round(max(reserve, 0.0), 4)


def reserve_schedule(
    S: float,
    i: float,
    n: int,
    qx_list: list,
    age: int,
    net_p: float,
    insurance_type: str = "term",
) -> list:
    """
    Таблица резервов по годам (от t=0 до t=n).

    Args:
        S: страховая сумма
        i: ставка дисконтирования
        n: срок договора
        qx_list: таблица смертности
        age: возраст застрахованного
        net_p: годовая нетто-премия
        insurance_type: тип страхования
    Returns:
        список словарей {year, age, reserve}
    """
    rows = []
    for t in range(n + 1):
        r = net_reserve(S, i, n, qx_list, age, t, net_p, insurance_type)
        rows.append({
            "year":    t,
            "age":     age + t,
            "reserve": r,
        })
    return rows


# ===========================================================================
# 4. НАКОПИТЕЛЬНОЕ СТРАХОВАНИЕ — ГРАФИК НАКОПЛЕНИЯ
# ===========================================================================

def accumulation_schedule(
    premium: float,
    rate: float,
    term: int,
    frequency: str = "yearly",
) -> list:
    """
    График накопления для накопительного страхования (endowment).

    Каждый период: accumulated = (accumulated + premium) * (1 + r_period)

    Args:
        premium: взнос за период
        rate: годовая процентная ставка (например 0.05)
        term: срок в годах
        frequency: 'yearly' или 'monthly'
    Returns:
        список словарей с данными по каждому периоду
    """
    periods_per_year = 12 if frequency == "monthly" else 1
    total_periods    = term * periods_per_year
    r_period         = rate / periods_per_year

    rows        = []
    accumulated = 0.0

    for t in range(1, total_periods + 1):
        accumulated  = (accumulated + premium) * (1 + r_period)
        interest     = accumulated - (accumulated / (1 + r_period)) - premium + \
                       (accumulated / (1 + r_period) * r_period)
        # упрощённо: проценты за период
        interest     = accumulated / (1 + r_period) * r_period

        year = math.ceil(t / periods_per_year)

        rows.append({
            "period":      t,
            "year":        year,
            "premium":     round(premium,      2),
            "accumulated": round(accumulated,  2),
            "interest":    round(interest,     2),
        })

    return rows


# ===========================================================================
# 5. РАСЧЁТ ПРЕМИИ ПО ТИПУ СТРАХОВАНИЯ (точка входа из routes.py)
# ===========================================================================

def calculate_premium_by_type(
    insurance_type: str,
    S: float,
    i: float,
    n: int,
    age: int,
    gender: str,
    qx_list: Optional[list] = None,
    inflation: float = 0.0,
    scenario: str = "baseline",
) -> dict:
    """
    Универсальная функция расчёта нетто-премии по типу страхования.

    Args:
        insurance_type: 'life', 'term', 'endowment', 'annuity', 'mixed'
        S: страховая сумма
        i: ставка дисконтирования
        n: срок в годах
        age: возраст застрахованного
        gender: 'M' или 'F'
        qx_list: таблица смертности (если None — строится аппроксимация)
        inflation: уровень инфляции
        scenario: 'baseline', 'pessimistic', 'optimistic'
    Returns:
        словарь с результатами расчёта
    """
    # Если таблица смертности не передана — строим линейную аппроксимацию
    if qx_list is None or len(qx_list) == 0:
        qx_list = _build_fallback_qx(gender)

    # Сценарный коэффициент
    scenario_mult = {"baseline": 1.0, "pessimistic": 1.5, "optimistic": 0.7}
    mult = scenario_mult.get(scenario, 1.0)
    qx_adjusted = [min(q * mult, 0.999) for q in qx_list]

    # Расчёт по типу
    if insurance_type in ("life", "term"):
        result = net_premium_term_life(S, i, n, qx_adjusted, age)
    elif insurance_type in ("endowment", "mixed"):
        result = net_premium_endowment(S, i, n, qx_adjusted, age)
    elif insurance_type == "annuity":
        result = _annuity_premium(S, i, n, qx_adjusted, age)
    else:
        result = net_premium_term_life(S, i, n, qx_adjusted, age)

    net_p = result["net_premium"]

    # Дисперсия и СКО
    qx_at_age = qx_adjusted[age] if age < len(qx_adjusted) else 0.02
    variance   = (S ** 2) * qx_at_age * (1 - qx_at_age)
    std_dev    = math.sqrt(variance)

    # Резерв на конец 1-го года
    ins_type_map = {
        "life": "term", "term": "term",
        "endowment": "endowment", "mixed": "endowment",
        "annuity": "term",
    }
    reserve_1yr = net_reserve(
        S, i, n, qx_adjusted, age, 1, net_p,
        ins_type_map.get(insurance_type, "term")
    )

    # Ожидаемая прибыль с учётом инфляции
    expected_profit = net_p * n - result.get("epv_total", result.get("epv", 0)) * (1 + inflation)

    return {
        "insurance_type":   insurance_type,
        "scenario":         scenario,
        "net_premium":      round(net_p,            2),
        "epv":              round(result.get("epv_total", result.get("epv", 0)), 2),
        "annuity":          round(result.get("annuity", 0), 4),
        "variance":         round(variance,          2),
        "std_dev":          round(std_dev,           2),
        "loss_probability": round(qx_at_age,         5),
        "reserve_1yr":      round(reserve_1yr,       2),
        "expected_profit":  round(expected_profit,   2),
        "survival_prob":    round(result.get("survival_prob", 0), 5),
    }


# ===========================================================================
# 6. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ===========================================================================

def _build_fallback_qx(gender: str = "M") -> list:
    """
    Строит упрощённую таблицу qx (возраст 0–110) при отсутствии реальных данных.
    Аппроксимация закона Гомпертца: q_x = a * exp(b * x).

    Мужчины: a=0.00022, b=0.097
    Женщины: a=0.00015, b=0.090  (более низкая смертность)
    """
    if gender == "F":
        a, b = 0.00015, 0.090
    else:
        a, b = 0.00022, 0.097

    qx = []
    for x in range(111):
        q = a * math.exp(b * x)
        qx.append(min(q, 1.0))
    return qx


def _annuity_premium(
    S: float,
    i: float,
    n: int,
    qx_list: list,
    age: int,
) -> dict:
    """
    Нетто-премия для пенсионного аннуитета (выплаты при дожитии).

    EPV аннуитета = S * sum_{t=1}^{n} t_p_x * v^t
    """
    v = 1 / (1 + i)

    epv_annuity = sum(
        survival_probability(qx_list, age, t) * (v ** t)
        for t in range(1, n + 1)
    ) * S

    ann = annuity_immediate(i, n)
    net_p = epv_annuity / ann if ann > 0 else 0.0

    return {
        "epv":        round(epv_annuity, 4),
        "annuity":    round(ann,         4),
        "net_premium": round(net_p,      4),
    }


def qx_from_db(age: int, gender: str) -> float:
    """
    Получает qx из базы данных (обёртка для использования в routes.py).
    Если таблица не загружена — возвращает значение из аппроксимации Гомпертца.

    Args:
        age: возраст
        gender: 'M' или 'F'
    Returns:
        значение qx
    """
    try:
        from models import MortalityTable, MortalityRate
        table = MortalityTable.query.filter_by(gender=gender)\
                    .order_by(MortalityTable.year.desc()).first()
        if table:
            rate = MortalityRate.query.filter_by(
                table_id=table.id, age=age
            ).first()
            if rate:
                return float(rate.qx)
    except Exception:
        pass

    # Fallback: Гомпертц
    fallback = _build_fallback_qx(gender)
    return fallback[age] if age < len(fallback) else 0.5


def full_qx_list_from_db(gender: str) -> list:
    """
    Загружает полную таблицу qx из БД для заданного пола.
    Индекс списка = возраст (0..110).
    Если данных нет — возвращает аппроксимацию Гомпертца.

    Args:
        gender: 'M' или 'F'
    Returns:
        список qx[0..110]
    """
    try:
        from models import MortalityTable, MortalityRate
        table = MortalityTable.query.filter_by(gender=gender)\
                    .order_by(MortalityTable.year.desc()).first()
        if table:
            rates = MortalityRate.query.filter_by(table_id=table.id)\
                        .order_by(MortalityRate.age).all()
            if rates:
                max_age = max(r.age for r in rates)
                qx_list = [0.0] * (max_age + 1)
                for r in rates:
                    qx_list[r.age] = float(r.qx)
                return qx_list
    except Exception:
        pass

    return _build_fallback_qx(gender)