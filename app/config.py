# app/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def _bool(env_key: str, default: bool = False) -> bool:
    """Parse booleans like 'True'/'False' safely from env."""
    val = os.getenv(env_key)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """
    Central app configuration.
    Values are pulled from .env; sensible fallbacks are provided for dev.
    """

    # --- Secrets ---
    SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or "dev-secret"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY

    # --- Database (mysqlclient) ---
    SQLALCHEMY_DATABASE_URI = (
        f"mysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Public base URL ---
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

    # --- File upload / QR paths ---
    PROJECT_ROOT = os.getcwd()
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")
    QR_FOLDER = os.path.join(PROJECT_ROOT, "static", "qr_codes")

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

    # --- Feature toggles ---
    ENABLE_SCHEDULER = _bool("ENABLE_SCHEDULER", False)

    # Ensure folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(QR_FOLDER, exist_ok=True)