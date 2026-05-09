import sqlite3
import os
from flask import g
from config import DATABASE_PATH


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS property_configs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            property_key    TEXT    NOT NULL UNIQUE,
            display_name    TEXT    NOT NULL,
            display_name_cn TEXT    NOT NULL,
            unit            TEXT    NOT NULL,
            mixing_model    TEXT    NOT NULL DEFAULT 'linear',
            min_value       REAL,
            max_value       REAL,
            sort_order      INTEGER NOT NULL DEFAULT 0
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            code            TEXT    UNIQUE,
            melting_point   REAL,
            oil_content     REAL,
            penetration     REAL,
            viscosity       REAL,
            color           REAL,
            cost_per_kg     REAL,
            description     TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS formulas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            description     TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS formula_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id      INTEGER NOT NULL,
            material_id     INTEGER NOT NULL,
            ratio           REAL    NOT NULL,
            FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE,
            FOREIGN KEY (material_id) REFERENCES materials(id)
        )
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_formula_items_formula
        ON formula_items(formula_id)
    """)

    _seed_property_configs(db)
    db.commit()


def _seed_property_configs(db):
    count = db.execute("SELECT COUNT(*) FROM property_configs").fetchone()[0]
    if count > 0:
        return

    props = [
        ("melting_point", "熔点 (Melting Point)", "熔点", "°C", "linear", 30, 80, 1),
        ("oil_content", "含油量 (Oil Content)", "含油量", "%", "linear", 0.1, 10.0, 2),
        ("penetration", "针入度 (Penetration)", "针入度", "1/10mm", "logarithmic", 5, 200, 3),
        ("viscosity", "粘度 (Viscosity)", "粘度", "mm²/s", "logarithmic", 2, 30, 4),
        ("color", "颜色 (Color)", "颜色", "Saybolt", "linear", -16, 30, 5),
    ]
    for key, dname, cn_name, unit, model, vmin, vmax, order in props:
        db.execute(
            "INSERT INTO property_configs (property_key, display_name, display_name_cn, unit, mixing_model, min_value, max_value, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (key, dname, cn_name, unit, model, vmin, vmax, order),
        )
