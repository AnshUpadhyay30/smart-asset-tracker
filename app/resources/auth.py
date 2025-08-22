# app/resources/auth.py
"""
Auth routes:
- POST /api/auth/register         (admin-only in real deployments; open here for dev)
- POST /api/auth/login            → returns JWT + role + first-login flags
- POST /api/auth/change-password  → requires JWT (used on first login)
- GET  /api/auth/me               → current user profile from JWT
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_cors import cross_origin
from app import db
from app.models import User  # imports User from app/models/user.py

auth_bp = Blueprint("auth", __name__)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _json():
    """Safely parse JSON body (never returns None)."""
    return request.get_json(silent=True) or {}

# ---------------------------------------------------------------------
# Register (dev only). In production, keep this ADMIN-only or remove.
# ---------------------------------------------------------------------
@auth_bp.route("/register", methods=["POST", "OPTIONS"])
@cross_origin(origins="http://localhost:4200", supports_credentials=True)
def register():
    # Handle preflight
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = _json()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "TECH").upper()  # for dev convenience

    if not name or not email or not password:
        return jsonify({"error": "name/email/password required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already exists"}), 400

    user = User(
        name=name,
        email=email,
        role=role,
        is_active=True,
        must_change_password=False,  # dev default; can set True if you want forced reset
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "registered"}), 201

# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------
@auth_bp.route("/login", methods=["POST", "OPTIONS"])
@cross_origin(origins="http://localhost:4200", supports_credentials=True)
def login():
    # Handle preflight
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = _json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email/password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    if not getattr(user, "is_active", True):
        return jsonify({"error": "account disabled"}), 403

    token = create_access_token(
        identity=str(user.id),  # store user id as string in JWT
        additional_claims={"role": user.role},
    )

    return jsonify({
        "access_token": token,
        "role": user.role,
        "must_change_password": getattr(user, "must_change_password", False),
        "is_active": getattr(user, "is_active", True),
        "name": user.name,
        "email": user.email,
    }), 200

# ---------------------------------------------------------------------
# Change password (used on first login / profile screen)
# ---------------------------------------------------------------------
@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    uid = int(get_jwt_identity())
    data = _json()
    new_pass = data.get("new_password") or ""

    # simple policy – adjust as needed
    if len(new_pass) < 8:
        return jsonify({"error": "min 8 characters required"}), 400

    user = User.query.get_or_404(uid)
    user.password_hash = generate_password_hash(new_pass)
    # stop forcing password reset after a successful change
    if hasattr(user, "must_change_password"):
        user.must_change_password = False

    db.session.commit()
    return jsonify({"message": "password updated"}), 200

# ---------------------------------------------------------------------
# Current user profile (handy for the app header)
# ---------------------------------------------------------------------
@auth_bp.get("/me")
@jwt_required()
def me():
    uid = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": getattr(user, "is_active", True),
        "must_change_password": getattr(user, "must_change_password", False),
    }), 200