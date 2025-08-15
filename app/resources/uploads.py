import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import jwt_required
from app.utils.file_utils import save_file

upload_bp = Blueprint("uploads", __name__)

# ✅ Upload a file
@upload_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    filename, error = save_file(file)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"message": "Upload successful", "filename": filename}), 201

# ✅ Securely serve uploaded files (auth required)
@upload_bp.route("/uploads/<filename>", methods=["GET"])
@jwt_required()
def get_uploaded_file(filename):
    upload_dir = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_dir, filename)