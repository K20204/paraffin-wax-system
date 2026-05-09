from flask import Blueprint, request, jsonify
from database import get_db
from engine.calculator import WaxCalculator

formulas_bp = Blueprint("formulas", __name__, url_prefix="/api/formulas")


def _safe_strip(val):
    return val.strip() if isinstance(val, str) else None


def _build_calculator():
    db = get_db()
    configs = {}
    for row in db.execute("SELECT * FROM property_configs ORDER BY sort_order").fetchall():
        r = dict(row)
        configs[r["property_key"]] = r
    return WaxCalculator(configs)


@formulas_bp.route("/", methods=["GET"])
def list_formulas():
    db = get_db()
    rows = db.execute(
        "SELECT f.*, COUNT(fi.id) as item_count FROM formulas f LEFT JOIN formula_items fi ON f.id = fi.formula_id GROUP BY f.id ORDER BY f.updated_at DESC"
    ).fetchall()
    return jsonify({"success": True, "items": [dict(r) for r in rows]})


@formulas_bp.route("/<int:id>", methods=["GET"])
def get_formula(id):
    db = get_db()
    row = db.execute("SELECT * FROM formulas WHERE id = ?", (id,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "配方不存在"}), 404

    items = db.execute(
        "SELECT fi.*, m.name as material_name, m.code as material_code FROM formula_items fi JOIN materials m ON fi.material_id = m.id WHERE fi.formula_id = ?",
        (id,),
    ).fetchall()

    result = dict(row)
    result["items"] = [dict(it) for it in items]

    if items:
        calc = _build_calculator()
        mat_rows = []
        ratios = []
        for it in items:
            m = db.execute("SELECT * FROM materials WHERE id = ?", (it["material_id"],)).fetchone()
            mat_rows.append(dict(m))
            ratios.append(it["ratio"])
        result["predicted_properties"] = calc.predict(mat_rows, ratios)
        result["total_cost"] = sum(r * m["cost_per_kg"] / 100 for r, m in zip(ratios, mat_rows) if m["cost_per_kg"])

    return jsonify({"success": True, "formula": result})


@formulas_bp.route("/", methods=["POST"])
def create_formula():
    db = get_db()
    data = request.get_json()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "名称不能为空"}), 400

    items = data.get("items", [])
    if items:
        total = sum(it["ratio"] for it in items)
        if abs(total - 100) > 0.5:
            return jsonify({"success": False, "error": f"比例之和必须为100%（当前 {total:.2f}%）"}), 400

    db.execute("INSERT INTO formulas (name, description) VALUES (?, ?)", (name, _safe_strip(data.get("description")) or None))
    fid = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    for it in items:
        db.execute("INSERT INTO formula_items (formula_id, material_id, ratio) VALUES (?, ?, ?)", (fid, it["material_id"], it["ratio"]))
    db.commit()

    return get_formula(fid)


@formulas_bp.route("/<int:id>", methods=["PUT"])
def update_formula(id):
    db = get_db()
    row = db.execute("SELECT * FROM formulas WHERE id = ?", (id,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "配方不存在"}), 404

    data = request.get_json()
    if "name" in data:
        db.execute("UPDATE formulas SET name=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (_safe_strip(data["name"]) or "", id))
    if "description" in data:
        db.execute("UPDATE formulas SET description=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (_safe_strip(data["description"]), id))

    if "items" in data:
        items = data["items"]
        total = sum(it["ratio"] for it in items)
        if abs(total - 100) > 0.5:
            return jsonify({"success": False, "error": f"比例之和必须为100%（当前 {total:.2f}%）"}), 400
        db.execute("DELETE FROM formula_items WHERE formula_id = ?", (id,))
        for it in items:
            db.execute("INSERT INTO formula_items (formula_id, material_id, ratio) VALUES (?, ?, ?)", (id, it["material_id"], it["ratio"]))

    db.commit()
    return get_formula(id)


@formulas_bp.route("/<int:id>", methods=["DELETE"])
def delete_formula(id):
    db = get_db()
    db.execute("DELETE FROM formulas WHERE id = ?", (id,))
    db.commit()
    return jsonify({"success": True})
