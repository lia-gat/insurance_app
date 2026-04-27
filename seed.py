from models import db, Client, Policy

def seed_data():
    if Client.query.first():
        return

    client1 = Client(name="Иван Иванов", age=30, gender="M")
    client2 = Client(name="Анна Смирнова", age=40, gender="F")

    db.session.add_all([client1, client2])
    db.session.commit()

    policy1 = Policy(client_id=1, term=10, premium=1000, interest_rate=0.05, sum_insured=10000)
    policy2 = Policy(client_id=2, term=15, premium=1500, interest_rate=0.04, sum_insured=20000)

    db.session.add_all([policy1, policy2])
    db.session.commit()