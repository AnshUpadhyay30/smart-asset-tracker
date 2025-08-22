# app/__init__.py

import logging
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from sqlalchemy import text

from .config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

from . import models  # noqa: E402


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    logging.basicConfig(level=logging.INFO)

    # ✅ CORS: Angular dev (http://localhost:4200) → Flask API (/api/*)
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:4200"]}},
        supports_credentials=False,  # cookies use नहीं कर रहे तो False
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type", "Authorization"],
        max_age=86400,
    )

    # ✅ Fallback so even error/401/404 responses carry CORS headers
    @app.after_request
    def _cors_fallback(resp):
        # origin vary handling
        resp.headers.setdefault("Vary", "Origin")
        # अगर flask-cors ने पहले से सेट नहीं किया, तो setdefault इसे जोड़ देगा
        resp.headers.setdefault("Access-Control-Allow-Origin", "http://localhost:4200")
        resp.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS")
        resp.headers.setdefault("Access-Control-Allow-Headers", "Authorization, Content-Type")
        return resp

    # ---------- extensions ----------
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # ---------- health ----------
    @app.get("/")
    def index():
        return {"message": "Smart Asset API is running. Hit /health for status."}

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        return {"status": "ok", "db": db_ok}

    @app.get("/favicon.ico")
    def favicon():
        return ("", 204)

    @app.get("/trigger-summary")
    def trigger_summary():
        from app.scheduler import send_due_summary
        send_due_summary()
        return {"message": "Summary triggered manually"}

    # ---------- blueprints ----------
    from app.resources.auth import auth_bp
    from app.resources.maintenance import maintenance_bp
    from app.routes.asset_routes import asset_bp
    from app.resources.uploads import upload_bp
    from app.resources.report_routes import report_bp
    from app.resources.dashboard import dashboard_bp
    from app.resources.qr_public import qr_public_bp
    from app.resources.admin_users import admin_users_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(maintenance_bp, url_prefix="/api")
    app.register_blueprint(asset_bp,        url_prefix="/api/assets")
    app.register_blueprint(upload_bp,       url_prefix="/api")
    app.register_blueprint(report_bp,       url_prefix="/api")
    app.register_blueprint(dashboard_bp,    url_prefix="/api/assets")
    app.register_blueprint(qr_public_bp,    url_prefix="/api")
    app.register_blueprint(admin_users_bp,  url_prefix="/api")

    # (Optional) Preflight catch-all — rarely needed, but safe:
    @app.route("/api/<path:_any>", methods=["OPTIONS"])
    def _preflight(_any):
        return ("", 204)

    if app.config.get("ENABLE_SCHEDULER"):
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app