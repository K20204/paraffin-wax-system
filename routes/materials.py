from flask import Blueprint, request, jsonify
from database import get_db
import sqlite3

materials_bp = Blueprint("materials", __name__, url_prefix="/api/materials")


def _safe_strip(val):
    return val.strip() if isinstance(val, str) else None


@materials_bp.route("/", methods=["GET"])
def list_materials():
    db = get_db()
    search = request.args.get("search", "")
    if search:
        rows = db.execute(
            "SELECT * FROM materials WHERE name LIKE ? OR code LIKE ? ORDER BY id",
            (f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM materials ORDER BY id").fetchall()
    return jsonify({"success": True, "items": [dict(r) for r in rows]})


@materials_bp.route("/<int:id>", methods=["GET"])
def get_material(id):
    db = get_db()
    row = db.execute("SELECT * FROM materials WHERE id = ?", (id,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "原料不存在"}), 404
    return jsonify({"success": True, "material": dict(row)})


@materials_bp.route("/", methods=["POST"])
def create_material():
    db = get_db()
    data = request.get_json()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "名称不能为空"}), 400

    try:
        db.execute(
            "INSERT INTO materials (name, code, melting_point, oil_content, penetration, viscosity, color, cost_per_kg, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                name,
                _safe_strip(data.get("code")) or None,
                data.get("melting_point"),
                data.get("oil_content"),
                data.get("penetration"),
                data.get("viscosity"),
                data.get("color"),
                data.get("cost_per_kg"),
                _safe_strip(data.get("description")) or None,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "代号已存在，请使用其他代号"}), 409
    row = db.execute("SELECT * FROM materials WHERE id = last_insert_rowid()").fetchone()
    return jsonify({"success": True, "material": dict(row)}), 201


@materials_bp.route("/<int:id>", methods=["PUT"])
def update_material(id):
    db = get_db()
    row = db.execute("SELECT * FROM materials WHERE id = ?", (id,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "原料不存在"}), 404

    data = request.get_json()
    fields = ["name", "code", "melting_point", "oil_content", "penetration", "viscosity", "color", "cost_per_kg", "description"]
    existing = dict(row)
    for f in fields:
        if f in data:
            existing[f] = data[f]
    existing["code"] = _safe_strip(existing.get("code")) or None
    existing["description"] = _safe_strip(existing.get("description")) or None

    try:
        db.execute(
            "UPDATE materials SET name=?, code=?, melting_point=?, oil_content=?, penetration=?, viscosity=?, color=?, cost_per_kg=?, description=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (existing["name"], existing["code"], existing["melting_point"], existing["oil_content"], existing["penetration"], existing["viscosity"], existing["color"], existing["cost_per_kg"], existing["description"], id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "代号已存在，请使用其他代号"}), 409
    row = db.execute("SELECT * FROM materials WHERE id = ?", (id,)).fetchone()
    return jsonify({"success": True, "material": dict(row)})


@materials_bp.route("/<int:id>", methods=["DELETE"])
def delete_material(id):
    db = get_db()
    used = db.execute("SELECT COUNT(*) FROM formula_items WHERE material_id = ?", (id,)).fetchone()[0]
    if used > 0:
        return jsonify({"success": False, "error": "该原料被配方引用，无法删除"}), 409
    db.execute("DELETE FROM materials WHERE id = ?", (id,))
    db.commit()
    return jsonify({"success": True})
