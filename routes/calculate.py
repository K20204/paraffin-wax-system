from flask import Blueprint, request, jsonify
from database import get_db
from engine.calculator import WaxCalculator

calculate_bp = Blueprint("calculate", __name__, url_prefix="/api/calculate")


def _build_calculator():
    db = get_db()
    configs = {}
    for row in db.execute("SELECT * FROM property_configs ORDER BY sort_order").fetchall():
        r = dict(row)
        configs[r["property_key"]] = r
    return WaxCalculator(configs)


def _get_materials_by_ids(db, ids):
    placeholders = ",".join("?" * len(ids))
    rows = db.execute(f"SELECT * FROM materials WHERE id IN ({placeholders})", ids).fetchall()
    id_map = {r["id"]: dict(r) for r in rows}
    return [id_map[mid] for mid in ids if mid in id_map]


@calculate_bp.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    mat_list = data.get("materials", [])
    if len(mat_list) < 2:
        return jsonify({"success": False, "error": "至少需要2种原料"}), 400

    db = get_db()
    calc = _build_calculator()
    mats = _get_materials_by_ids(db, [m["id"] for m in mat_list])
    ratios = [m["ratio"] for m in mat_list]

    props = calc.predict(mats, ratios)
    total_cost = sum(r * m["cost_per_kg"] / 100 for r, m in zip(ratios, mats) if m["cost_per_kg"])

    return jsonify({"success": True, "properties": props, "total_cost": total_cost})


@calculate_bp.route("/ratio", methods=["POST"])
def calculate_ratio():
    data = request.get_json()
    material_ids = data.get("material_ids", [])
    targets = data.get("targets", {})
    locked_ratios = data.get("locked_ratios", {})

    if len(material_ids) < 2:
        return jsonify({"success": False, "error": "至少需要2种原料"}), 400
    if not targets:
        return jsonify({"success": False, "error": "至少需要1个目标属性"}), 400

    db = get_db()
    calc = _build_calculator()
    mats = _get_materials_by_ids(db, material_ids)
    if len(mats) < 2:
        return jsonify({"success": False, "error": "有效的原料不足2个"}), 400

    locked = {}
    if locked_ratios:
        for k, v in locked_ratios.items():
            mid = int(k)
            if mid in material_ids:
                locked[material_ids.index(mid)] = v

    result = calc.calculate_ratios(mats, targets, locked)
    if result is None:
        return jsonify({"success": False, "error": "无法计算配比，请检查目标值是否合理"}), 400

    return jsonify({"success": True, "ratios": result["ratios"], "predicted": result["predicted"], "total_error": result["total_error"]})


@calculate_bp.route("/optimize", methods=["POST"])
def optimize():
    data = request.get_json()
    material_ids = data.get("material_ids", [])
    target_ranges = data.get("target_ranges", {})
    max_components = data.get("max_components", 4)
    cost_weight = data.get("cost_weight", 0.3)

    if len(material_ids) < 2:
        return jsonify({"success": False, "error": "至少需要2种原料"}), 400
    if not target_ranges:
        return jsonify({"success": False, "error": "至少需要1个目标范围"}), 400

    db = get_db()
    calc = _build_calculator()
    mats = _get_materials_by_ids(db, material_ids)
    if len(mats) < 2:
        return jsonify({"success": False, "error": "有效的原料不足2个"}), 400

    results = calc.optimize(mats, target_ranges, cost_weight, max_components)
    return jsonify({"success": True, "results": results})
