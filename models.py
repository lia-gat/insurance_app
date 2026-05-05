from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(150), nullable=False)   # ФИО клиента
    birth_date = db.Column(db.Date,        nullable=False)   # Дата рождения
    gender     = db.Column(db.String(10))                    # M / F
    phone      = db.Column(db.String(20))                    # Телефон
    email      = db.Column(db.String(120))                   # Email
    address    = db.Column(db.String(255))                   # Адрес
    status     = db.Column(db.String(20),  default="alive")  # alive / deceased
    death_date = db.Column(db.Date,        nullable=True)    # Дата смерти

    # cascade="all, delete-orphan" — при удалении клиента удаляются все его договоры
    policies = db.relationship(
        'Policy', backref='client', lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def total_sum_insured(self):
        return sum(p.sum_insured or 0 for p in self.policies)


class Policy(db.Model):
    id                   = db.Column(db.Integer,     primary_key=True)
    client_id            = db.Column(db.Integer,     db.ForeignKey('client.id'),  nullable=False)
    contract_number      = db.Column(db.String(50),  unique=True, nullable=False) # Номер договора
    issue_date           = db.Column(db.Date,        nullable=False)              # Дата заключения
    insurance_type       = db.Column(db.String(50))                               # life / endowment / term / annuity / mixed
    term_years           = db.Column(db.Integer)                                  # Срок (лет)
    premium              = db.Column(db.Float)                                    # Размер взноса
    premium_frequency    = db.Column(db.String(20))                               # monthly / yearly
    interest_rate        = db.Column(db.Float)                                    # Ставка доходности
    sum_insured          = db.Column(db.Float)                                    # Страховая сумма
    beneficiary_name     = db.Column(db.String(150))                              # Выгодоприобретатель
    beneficiary_relation = db.Column(db.String(50))                               # Степень родства
    beneficiary_phone    = db.Column(db.String(20))                               # Телефон выгодоприобретателя
    beneficiary_email    = db.Column(db.String(120))                              # Email выгодоприобретателя
    status               = db.Column(db.String(20),  default="active")            # active / closed / expired

    payments = db.relationship('Payment',       backref='policy', lazy=True, cascade="all, delete-orphan")
    claims   = db.relationship('Claim',         backref='policy', lazy=True, cascade="all, delete-orphan")
    history  = db.relationship('PolicyHistory', backref='policy', lazy=True, cascade="all, delete-orphan")
    reserves = db.relationship('Reserve',       backref='policy', lazy=True, cascade="all, delete-orphan")


class Payment(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    policy_id    = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    amount       = db.Column(db.Float,   nullable=False)
    payment_date = db.Column(db.Date,    nullable=False)
    payment_type = db.Column(db.String(20), default="premium")   # premium / penalty / partial_withdrawal
    status       = db.Column(db.String(20), default="confirmed") # confirmed / pending / overdue


class Claim(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    policy_id       = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    claim_date      = db.Column(db.Date,    nullable=True)    # ← ДОБАВЛЕНО: дата страхового случая
    claim_amount    = db.Column(db.Float)                     # Заявленная сумма
    approved_amount = db.Column(db.Float)                     # Утверждённая сумма
    reason          = db.Column(db.String(100))               # death / maturity / surrender


class PolicyHistory(db.Model):
    id          = db.Column(db.Integer,     primary_key=True)
    policy_id   = db.Column(db.Integer,     db.ForeignKey('policy.id'), nullable=False)
    change_date = db.Column(db.Date)
    field_name  = db.Column(db.String(50),  nullable=False)  # Название изменённого поля
    old_value   = db.Column(db.String(255))                  # Старое значение (увеличили до 255)
    new_value   = db.Column(db.String(255))                  # Новое значение
    value_type  = db.Column(db.String(20))                   # str / float / int / date


class MortalityTable(db.Model):
    id         = db.Column(db.Integer,      primary_key=True)
    table_name = db.Column(db.String(100))
    gender     = db.Column(db.String(10))   # M / F
    year       = db.Column(db.Integer)

    rates = db.relationship('MortalityRate', backref='table', lazy=True, cascade="all, delete-orphan")


class MortalityRate(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('mortality_table.id'), nullable=False)
    age      = db.Column(db.Integer)
    qx       = db.Column(db.Float)


class EconomicParameters(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    effective_date = db.Column(db.Date)
    inflation_rate = db.Column(db.Float)
    discount_rate  = db.Column(db.Float)


class Reserve(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    policy_id      = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    date           = db.Column(db.Date)
    reserve_amount = db.Column(db.Float)