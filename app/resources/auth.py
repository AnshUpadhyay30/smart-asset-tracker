# app/resources/auth.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)

# ----------------------------
# User Registration
# ----------------------------
@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "TECH")  # default TECH if not given

    if not all([name, email, password]):
        return jsonify({"error": "name/email/password required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already exists"}), 400

    u = User(
        name=name,
        email=email,
        role=role,
        password_hash=generate_password_hash(password)
    )
    db.session.add(u)
    db.session.commit()

    return {"message": "registered"}, 201


# ----------------------------
# User Login
# ----------------------------
@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "email/password required"}), 400

    u = User.query.filter_by(email=email).first()

    if not u or not check_password_hash(u.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    # FIX: Convert identity to string to avoid "Subject must be a string" error
    token = create_access_token(identity=str(u.id), additional_claims={"role": u.role})

    return {"access_token": token, "role": u.role}


"""
Note:
When you later retrieve the identity from the token:

from flask_jwt_extended import get_jwt_identity
user_id = int(get_jwt_identity())  # convert back to int if needed
"""