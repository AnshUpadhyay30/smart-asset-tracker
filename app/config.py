# app/config.py

import os
from dotenv import load_dotenv

# ✅ Load environment variables from .env file
load_dotenv()

class Config:
    # 🔐 JWT secret key for authentication
    SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    # 🛢️ MySQL DB connection string
    SQLALCHEMY_DATABASE_URI = (
        f"mysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable event system overhead

    # 🌐 Public base URL for generating QR links etc.
    PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL')

    # 📁 File upload config
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB max upload size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

    # 🕐 Scheduler toggle (useful for local dev vs prod)
    ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "False") == "True"