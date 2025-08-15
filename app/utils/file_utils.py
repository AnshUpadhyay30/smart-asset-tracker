import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

# ✅ Extension check
def allowed_file(filename):
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", set())
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

# ✅ File save logic
def save_file(file_obj, prefix="file"):
    if not file_obj or not allowed_file(file_obj.filename):
        return None, "Invalid file or extension not allowed"

    # Secure filename to prevent path attacks
    filename = secure_filename(file_obj.filename)

    # Create uploads folder if not exists
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    # Add timestamp for uniqueness
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{prefix}_{timestamp}_{filename}"

    file_path = os.path.join(upload_dir, filename)
    try:
        file_obj.save(file_path)
        return filename, None
    except Exception as e:
        return None, str(e)