from datetime import date
from models import db, Client, Policy, Payment, Claim, PolicyHistory, Reserve
from app import create_app

def seed_data():
    if Client.query.first():
        return


    c1 = Client(full_name="Иванов Алексей Дмитриевич",
                birth_date=date(1989, 5, 14), gender="M",
                phone="+7 (495) 111-22-33", email="ivanov.alexey@mail.ru",
                address="г. Москва, ул. Ленина, д. 5, кв. 12", status="alive")

    c2 = Client(full_name="Смирнова Елена Сергеевна",
                birth_date=date(1999, 7, 22), gender="F",
                phone="+7 (812) 222-33-44", email="smirnova.elena@gmail.com",
                address="г. Санкт-Петербург, пр. Невский, д. 44", status="alive")

    c3 = Client(full_name="Петров Николай Васильевич",
                birth_date=date(1984, 11, 5), gender="M",
                phone="+7 (383) 333-44-55", email="petrov.nv@yandex.ru",
                address="г. Новосибирск, ул. Советская, д. 18", status="alive")

    c4 = Client(full_name="Козлова Марина Андреевна",
                birth_date=date(1994, 6, 30), gender="F",
                phone="+7 (343) 444-55-66", email="kozlova.m@mail.ru",
                address="г. Екатеринбург, ул. Мира, д. 7, кв. 201", status="alive")

    c5 = Client(full_name="Новиков Сергей Игоревич",
                birth_date=date(1979, 9, 17), gender="M",
                phone="+7 (863) 555-66-77", email="novikov.si@inbox.ru",
                address="г. Ростов-на-Дону, пер. Садовый, д. 2", status="alive")

    c6 = Client(full_name="Морозова Татьяна Павловна",
                birth_date=date(1969, 1, 8), gender="F",
                phone="+7 (846) 666-77-88", email="morozova.tp@yandex.ru",
                address="г. Самара, ул. Чапаевская, д. 33, кв. 5", status="alive")

    c7 = Client(full_name="Лебедев Виктор Юрьевич",
                birth_date=date(1954, 8, 19), gender="M",
                phone="+7 (843) 999-00-11", email="lebedev.vy@inbox.ru",
                address="г. Казань, ул. Баумана, д. 17",
                status="deceased", death_date=date(2023, 5, 12))

    c8 = Client(full_name="Волков Андрей Михайлович",
                birth_date=date(1997, 4, 25), gender="M",
                phone="+7 (351) 777-88-99", email="volkov.am@gmail.com",
                address="г. Челябинск, ул. Победы, д. 11", status="alive")

    db.session.add_all([c1, c2, c3, c4, c5, c6, c7, c8])
    db.session.flush()


    p1 = Policy(client_id=c1.id, contract_number="TERM-2024-001",
                issue_date=date(2024, 1, 1), insurance_type="term",
                term_years=20, premium=1420.85, premium_frequency="yearly",
                interest_rate=0.0, sum_insured=100000.00,
                beneficiary_name="Иванова Светлана Александровна",
                beneficiary_relation="spouse",
                beneficiary_phone="+7 (495) 111-22-34", status="active")

    p2 = Policy(client_id=c1.id, contract_number="ENDOW-2024-002",
                issue_date=date(2024, 1, 1), insurance_type="endowment",
                term_years=20, premium=3471.38, premium_frequency="yearly",
                interest_rate=5.0, sum_insured=100000.00,
                beneficiary_name="Иванова Светлана Александровна",
                beneficiary_relation="spouse", status="active")

    p3 = Policy(client_id=c2.id, contract_number="ENDOW-2024-003",
                issue_date=date(2024, 1, 1), insurance_type="endowment",
                term_years=3, premium=51266.10, premium_frequency="yearly",
                interest_rate=25.0, sum_insured=100000.00, status="active")

    p4 = Policy(client_id=c3.id, contract_number="TERM-2020-004",
                issue_date=date(2020, 3, 1), insurance_type="term",
                term_years=15, premium=5800.00, premium_frequency="yearly",
                interest_rate=0.0, sum_insured=200000.00, status="active")

    p5 = Policy(client_id=c4.id, contract_number="ENDOW-2024-005",
                issue_date=date(2024, 1, 1), insurance_type="endowment",
                term_years=15, premium=13000.00, premium_frequency="yearly",
                interest_rate=5.0, sum_insured=200000.00,
                beneficiary_name="Козлов Дмитрий Артёмович",
                beneficiary_relation="child", status="active")

    p6 = Policy(client_id=c5.id, contract_number="TERM-2024-006",
                issue_date=date(2024, 1, 1), insurance_type="term",
                term_years=10, premium=29500.00, premium_frequency="yearly",
                interest_rate=0.0, sum_insured=300000.00, status="active")

    p7 = Policy(client_id=c6.id, contract_number="ENDOW-2024-007",
                issue_date=date(2024, 1, 1), insurance_type="endowment",
                term_years=10, premium=14200.00, premium_frequency="yearly",
                interest_rate=5.0, sum_insured=150000.00, status="active")

    p8 = Policy(client_id=c7.id, contract_number="LIFE-2005-008",
                issue_date=date(2005, 3, 1), insurance_type="life",
                term_years=25, premium=15000.00, premium_frequency="yearly",
                interest_rate=0.0, sum_insured=300000.00,
                beneficiary_name="Лебедева Зинаида Павловна",
                beneficiary_relation="spouse",
                beneficiary_phone="+7 (843) 999-00-12", status="closed")

    p9 = Policy(client_id=c8.id, contract_number="ENDOW-2023-009",
                issue_date=date(2023, 1, 1), insurance_type="endowment",
                term_years=5, premium=1000.00, premium_frequency="yearly",
                interest_rate=5.0, sum_insured=5801.91, status="active")

    db.session.add_all([p1, p2, p3, p4, p5, p6, p7, p8, p9])
    db.session.flush()


    payments = []

    for pol, amt in [(p1, 1420.85), (p2, 3471.38), (p3, 51266.10)]:
        payments.append(Payment(policy_id=pol.id, amount=amt,
                                payment_date=date(2024, 1, 10),
                                payment_type="premium", status="confirmed"))

    for yr in range(2020, 2024):
        payments.append(Payment(policy_id=p4.id, amount=5800.00,
                                payment_date=date(yr, 3, 1),
                                payment_type="premium", status="confirmed"))

    for pol, amt in [(p5, 13000.00), (p6, 29500.00), (p7, 14200.00)]:
        payments.append(Payment(policy_id=pol.id, amount=amt,
                                payment_date=date(2024, 1, 20),
                                payment_type="premium", status="confirmed"))

    for yr in range(2005, 2023):
        payments.append(Payment(policy_id=p8.id, amount=15000.00,
                                payment_date=date(yr, 3, 1),
                                payment_type="premium", status="confirmed"))

    for yr in [2023, 2024]:
        payments.append(Payment(policy_id=p9.id, amount=1000.00,
                                payment_date=date(yr, 1, 5),
                                payment_type="premium", status="confirmed"))

    db.session.add_all(payments)


    db.session.add(Claim(
        policy_id=p8.id, claim_date=date(2023, 5, 20),
        claim_amount=300000.00, approved_amount=300000.00, reason="death"
    ))


    db.session.add(PolicyHistory(
        policy_id=p8.id, change_date=date(2023, 5, 20),
        field_name="status", old_value="active", new_value="closed", value_type="str"
    ))


    today = date.today()
    reserves = [
        Reserve(policy_id=p1.id, date=today, reserve_amount=883.36),    # term, t=1
        Reserve(policy_id=p2.id, date=today, reserve_amount=3940.00),   # endowment, t=1
        Reserve(policy_id=p5.id, date=today, reserve_amount=3940.00),   # сценарий x=30
        Reserve(policy_id=p6.id, date=today, reserve_amount=14850.00),  # сценарий x=45
        Reserve(policy_id=p7.id, date=today, reserve_amount=9120.00),   # сценарий x=55
    ]
    db.session.add_all(reserves)

    db.session.commit()

app = create_app()

with app.app_context():
    seed_data()
    print("Данные загружены")