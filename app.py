"""
app.py — Точка входа Flask-приложения.

Запуск:
    python app.py

Переменные окружения (опционально):
    DATABASE_URL  — строка подключения к БД (по умолчанию SQLite)
    SECRET_KEY    — секретный ключ Flask (по умолчанию dev-ключ)
    FLASK_DEBUG   — '1' для режима отладки
"""

import os
from flask import Flask
from models import db


def create_app() -> Flask:
    """Фабрика приложения."""

    app = Flask(__name__)

    # -----------------------------------------------------------------------
    # Конфигурация
    # -----------------------------------------------------------------------
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # База данных: SQLite по умолчанию, можно переключить на PostgreSQL
    default_db = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'insurance.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -----------------------------------------------------------------------
    # Инициализация расширений
    # -----------------------------------------------------------------------
    db.init_app(app)

    # -----------------------------------------------------------------------
    # Регистрация blueprints
    # -----------------------------------------------------------------------
    from routes import main, client_bp, policy_bp, payment_bp, claim_bp

    app.register_blueprint(main)
    app.register_blueprint(client_bp)
    app.register_blueprint(policy_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(claim_bp)

    # -----------------------------------------------------------------------
    # Создание таблиц при первом запуске
    # -----------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Запуск напрямую: python app.py
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    application = create_app()
    debug_mode  = os.environ.get('FLASK_DEBUG', '1') == '1'
    application.run(debug=debug_mode, host='0.0.0.0', port=5000)