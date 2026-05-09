from flask import Blueprint, request, jsonify
from database import get_db

properties_bp = Blueprint("properties", __name__, url_prefix="/api/properties")


@properties_bp.route("/", methods=["GET"])
def list_properties():
    db = get_db()
    rows = db.execute("SELECT * FROM property_configs ORDER BY sort_order").fetchall()
    return jsonify({"success": True, "properties": [dict(r) for r in rows]})


@properties_bp.route("/<property_key>", methods=["PUT"])
def update_property(property_key):
    db = get_db()
    row = db.execute("SELECT * FROM property_configs WHERE property_key = ?", (property_key,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "属性不存在"}), 404

    data = request.get_json()
    allowed = ["linear", "logarithmic"]
    if "mixing_model" in data:
        if data["mixing_model"] not in allowed:
            return jsonify({"success": False, "error": f"混合模型必须是 {allowed} 之一"}), 400
        db.execute("UPDATE property_configs SET mixing_model=? WHERE property_key=?", (data["mixing_model"], property_key))
        db.commit()

    row = db.execute("SELECT * FROM property_configs WHERE property_key = ?", (property_key,)).fetchone()
    return jsonify({"success": True, "property": dict(row)})
