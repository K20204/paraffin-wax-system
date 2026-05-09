from database import get_db


def seed_materials():
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM materials").fetchone()[0]
    if count > 0:
        return

    materials = [
        # (name, code, mp, oil, pen, visc, color, cost)
        ("54# 半精炼石蜡", "SR-54", 54.0, 1.5, 18, 4.2, 28, 7.5),
        ("56# 半精炼石蜡", "SR-56", 56.0, 1.3, 16, 4.5, 28, 8.0),
        ("58# 半精炼石蜡", "SR-58", 58.0, 1.2, 15, 4.8, 27, 8.5),
        ("60# 半精炼石蜡", "SR-60", 60.0, 1.0, 14, 5.0, 27, 9.0),
        ("62# 半精炼石蜡", "SR-62", 62.0, 0.8, 12, 5.3, 26, 9.5),
        ("58# 全精炼石蜡", "FR-58", 58.0, 0.5, 13, 4.6, 29, 10.0),
        ("60# 全精炼石蜡", "FR-60", 60.0, 0.4, 12, 4.9, 29, 10.5),
        ("62# 全精炼石蜡", "FR-62", 62.0, 0.3, 10, 5.2, 28, 11.0),
        ("64# 全精炼石蜡", "FR-64", 64.0, 0.3, 9, 5.5, 28, 11.5),
        ("微晶蜡", "MC-70", 70.0, 2.0, 25, 12.0, 20, 14.0),
    ]

    for name, code, mp, oil, pen, visc, color, cost in materials:
        db.execute(
            "INSERT INTO materials (name, code, melting_point, oil_content, penetration, viscosity, color, cost_per_kg) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, code, mp, oil, pen, visc, color, cost),
        )
    db.commit()
