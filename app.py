import os
from flask import Flask
from models import db

def create_app() -> Flask:

    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    default_db = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'insurance.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from translations import LABELS, translate
    app.jinja_env.globals['LABELS'] = LABELS
    app.jinja_env.filters['tr'] = translate

    from routes import main, client_bp, policy_bp, payment_bp, claim_bp, mortality_bp

    app.register_blueprint(main)
    app.register_blueprint(client_bp)
    app.register_blueprint(policy_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(claim_bp)
    app.register_blueprint(mortality_bp)

    with app.app_context():
        db.create_all()
        _seed_mortality_table(app)
        

    return app


def _seed_mortality_table(app: Flask) -> None:
    """
    Загружает упрощённую таблицу смертности (Гомпертц-аппроксимация)
    если в БД ещё нет ни одной таблицы.
    Используется как fallback для демо-режима.
    """
    from models import MortalityTable, MortalityRate
    from actuarial import _build_fallback_qx
    from datetime import date

    if MortalityTable.query.first():
        return  # таблица уже загружена — не перезаписываем

    for gender in ('M', 'F'):
        table = MortalityTable(
            table_name=f"Гомпертц-аппроксимация ({gender})",
            gender=gender,
            year=date.today().year,
        )
        db.session.add(table)
        db.session.flush()  # получаем table.id до commit

        qx_list = _build_fallback_qx(gender)
        for age, qx in enumerate(qx_list):
            rate = MortalityRate(
                table_id=table.id,
                age=age,
                qx=round(qx, 8),
            )
            db.session.add(rate)

    db.session.commit()
    print("[app] Таблица смертности инициализирована (Гомпертц-аппроксимация).")


if __name__ == '__main__':
    application = create_app()
    debug_mode  = os.environ.get('FLASK_DEBUG', '1') == '1'
    application.run(debug=debug_mode, host='0.0.0.0', port=5000)