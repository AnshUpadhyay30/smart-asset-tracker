# app/__init__.py

import logging
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from sqlalchemy import text
from .config import Config  # Load configuration from .env

# ✅ Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# ⛔ Avoid circular imports by importing models after initializing extensions
from . import models  # noqa: E402

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ✅ Logging setup (ensure logs show in all environments)
    logging.basicConfig(level=logging.INFO)

    # ✅ Enable CORS for frontend-backend API calls
    CORS(app)

    # ✅ Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # ─────────────────────────────────────────────────────────────
    # 🟢 Health check endpoints (basic monitoring and testing)
    # ─────────────────────────────────────────────────────────────
    @app.get("/")
    def index():
        return {"message": "Smart Asset API is running. Hit /health for status."}

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))  # DB connection check
            db_ok = True
        except Exception:
            db_ok = False
        return {"status": "ok", "db": db_ok}

    @app.get("/favicon.ico")
    def favicon():
        return ("", 204)

    # ─────────────────────────────────────────────────────────────
    # 🧪 Manual trigger for daily summary (for testing purposes)
    # ─────────────────────────────────────────────────────────────
    @app.get("/trigger-summary")
    def trigger_summary():
        """Manually trigger maintenance summary (used in dev testing)"""
        from app.scheduler import send_due_summary
        send_due_summary()
        return {"message": "Summary triggered manually"}

    # ─────────────────────────────────────────────────────────────
    # 🔗 Register all API Blueprints (modular routing)
    # ─────────────────────────────────────────────────────────────
    from app.resources.auth import auth_bp                     # 🔐 Login/Register
    from app.resources.maintenance import maintenance_bp       # 🛠️ Maintenance logs
    from app.routes.asset_routes import asset_bp               # 🧾 Asset CRUD
    from app.resources.uploads import upload_bp                # 📤 File upload/download
    from app.resources.report_routes import report_bp          # 📊 Reports & CSV export

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(maintenance_bp, url_prefix="/api")
    app.register_blueprint(asset_bp, url_prefix="/api/assets")
    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(report_bp, url_prefix="/api")

    # ─────────────────────────────────────────────────────────────
    # ⏰ Start APScheduler if enabled in .env
    # ─────────────────────────────────────────────────────────────
    if app.config.get("ENABLE_SCHEDULER"):
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app