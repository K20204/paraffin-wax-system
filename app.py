from flask import Flask, render_template
from config import SECRET_KEY, DEBUG
from database import init_db, get_db
from seed_data import seed_materials


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    with app.app_context():
        init_db(app)
        seed_materials()

    from routes.materials import materials_bp
    from routes.formulas import formulas_bp
    from routes.calculate import calculate_bp
    from routes.properties import properties_bp

    app.register_blueprint(materials_bp)
    app.register_blueprint(formulas_bp)
    app.register_blueprint(calculate_bp)
    app.register_blueprint(properties_bp)

    @app.route("/")
    def index():
        db = get_db()
        mat_count = db.execute("SELECT COUNT(*) FROM materials").fetchone()[0]
        formula_count = db.execute("SELECT COUNT(*) FROM formulas").fetchone()[0]
        recent = db.execute(
            "SELECT id, name, created_at FROM formulas ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        return render_template(
            "index.html", mat_count=mat_count, formula_count=formula_count, recent=recent
        )

    @app.route("/materials")
    def materials_page():
        return render_template("materials.html")

    @app.route("/formulas")
    def formulas_page():
        return render_template("formulas.html")

    @app.route("/formulas/<int:id>")
    def formula_detail(id):
        return render_template("formula_detail.html", formula_id=id)

    @app.route("/predict")
    def predict_page():
        return render_template("predict.html")

    @app.route("/calculate")
    def calculate_page():
        return render_template("calculate.html")

    @app.route("/optimize")
    def optimize_page():
        return render_template("optimize.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=DEBUG, port=5000)
