# app/resources/admin_users.py
"""
Admin-only user management endpoints:
- POST   /api/admin/users                      → create single user (with optional username/temp_password)
- POST   /api/admin/users/bulk                 → bulk create users (array or CSV)
- GET    /api/admin/users/suggest-username     → suggest a unique username based on a name/email
- GET    /api/admin/users                      → list users
- PUT    /api/admin/users/<id>/role            → change role
- PUT    /api/admin/users/<id>/status          → activate/deactivate
- POST   /api/admin/users/<id>/reset-password  → issue new temp password (returns temp_password)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.security import generate_password_hash
from app import db
from app.models import User

# Optional mailer (best-effort)
try:
    from app.utils.mailer import send_temp_password_email
except Exception:
    def send_temp_password_email(email, name, temp):
        return False

admin_users_bp = Blueprint("admin_users", __name__)

def _require_admin():
    claims = get_jwt() or {}
    return claims.get("role") == "ADMIN"

# ---------------- util: username generation ----------------
def _slugify(s: str) -> str:
    import re
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", ".", s).strip(".")
    return s or "user"

def _next_username(base: str) -> str:
    base = _slugify(base)
    candidate = base
    i = 1
    while User.query.filter_by(username=candidate).first() is not None:
        i += 1
        candidate = f"{base}{i}"
    return candidate

# ---------------- suggest username ----------------
@admin_users_bp.get("/admin/users/suggest-username")
@jwt_required()
def suggest_username():
    if not _require_admin():
        return jsonify({"error": "Forbidden"}), 403

    name = (request.args.get("name") or "").strip()
    email = (request.args.get("email") or "").strip().lower()
    base = name or email.split("@")[0]
    if not base:
        return jsonify({"error": "name or email required"}), 400
    return jsonify({"username": _next_username(base)}), 200

# ---------------- single create ----------------
@admin_users_bp.post("/admin/users")
@jwt_required()
def admin_create_user():
    if not _require_admin():
        return jsonify({"error": "Forbidden"}), 403

    body = request.get_json() or {}
    name  = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    role  = (body.get("role") or "TECH").upper()
    username = (body.get("username") or "").strip().lower()
    temp_password = (body.get("temp_password") or "").strip() or None

    if not name or not email:
        return jsonify({"error": "name & email required"}), 400
    if role not in ("ADMIN", "MANAGER", "TECH"):
        return jsonify({"error": "invalid role"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already exists"}), 400

    # username normalize/suggest
    if username:
        from re import match
        if not match(r"^[a-z0-9_.-]{3,60}$", username):
            return jsonify({"error": "invalid username format"}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "username already exists"}), 400
    else:
        base = name or email.split("@")[0]
        username = _next_username(base)

    # temp password (generate if not supplied)
    if not temp_password:
        import secrets, string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        temp_password = "".join(secrets.choice(alphabet) for _ in range(12))

    u = User(
        name=name,
        email=email,
        username=username,
        role=role,
        is_active=True,
        must_change_password=True,
        password_hash=generate_password_hash(temp_password),
        # ✅ persist so admin-table hamesha dikha sake
        last_temp_password=temp_password,
    )
    db.session.add(u)
    db.session.commit()

    # best-effort email
    try:
        send_temp_password_email(email, name, temp_password)
    except Exception:
        pass

    return jsonify({
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "username": u.username,
        "role": u.role,
        "is_active": u.is_active,
        "must_change_password": u.must_change_password,
        "temp_password": temp_password  # convenience for immediate UI
    }), 201

# ---------------- bulk create ----------------
@admin_users_bp.post("/admin/users/bulk")
@jwt_required()
def admin_bulk_create():
    if not _require_admin():
        return jsonify({"error": "Forbidden"}), 403

    body = request.get_json() or {}

    rows = []
    if isinstance(body.get("users"), list):
        rows = body["users"]
    elif isinstance(body.get("csv"), str):
        import csv, io
        f = io.StringIO(body["csv"])
        for r in csv.DictReader(f):
            rows.append({
                "name": r.get("name"),
                "email": r.get("email"),
                "role": (r.get("role") or "TECH").upper(),
                "username": r.get("username") or None
            })
    else:
        return jsonify({"error": "Provide 'users' array or 'csv' string"}), 400

    created, errors = [], []

    import secrets, string, re
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    USER_RE = re.compile(r"^[a-z0-9_.-]{3,60}$")

    for i, item in enumerate(rows, start=1):
        try:
            name  = (item.get("name") or "").strip()
            email = (item.get("email") or "").strip().lower()
            role  = (item.get("role") or "TECH").upper()
            username = (item.get("username") or "").strip().lower()

            if not name or not email:
                raise ValueError("name & email required")
            if role not in ("ADMIN", "MANAGER", "TECH"):
                raise ValueError("invalid role")
            if User.query.filter_by(email=email).first():
                raise ValueError("email exists")

            if username:
                if not USER_RE.match(username):
                    raise ValueError("invalid username format")
                if User.query.filter_by(username=username).first():
                    raise ValueError("username exists")
            else:
                base = name or email.split("@")[0]
                username = _next_username(base)

            temp_password = "".join(secrets.choice(alphabet) for _ in range(12))

            u = User(
                name=name,
                email=email,
                username=username,
                role=role,
                is_active=True,
                must_change_password=True,
                password_hash=generate_password_hash(temp_password),
                last_temp_password=temp_password,   # ✅ persist
            )
            db.session.add(u)
            db.session.flush()  # get id

            created.append({
                "row": i, "id": u.id, "name": name, "email": email,
                "username": username, "role": role, "temp_password": temp_password
            })
        except Exception as e:
            errors.append({"row": i, "email": item.get("email"), "error": str(e)})

    db.session.commit()

    # optional email
    for c in created:
        try:
            send_temp_password_email(c["email"], c["name"], c["temp_password"])
        except Exception:
            pass

    return jsonify({"created": created, "errors": errors}), 200

# ---------------- list / role / status / reset ----------------
@admin_users_bp.get("/admin/users")
@jwt_required()
def admin_list_users():
    if not _require_admin():
        return jsonify({"error": "Forbidden"}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    # ✅ last_temp_password include so UI refresh par bhi dikhe
    return jsonify([{
        "id": x.id,
        "name": x.name,
        "email": x.email,
        "username": x.username,
        "role": x.role,
        "is_active": x.is_active,
        "must_change_password": x.must_change_password,
        "last_temp_password": getattr(x, "last_temp_password", None),
    } for x in users]), 200

@admin_users_bp.put("/admin/users/<int:user_id>/role")
@jwt_required()
def admin_update_role(user_id):
    if not _require_admin():
        return jsonify({"error": "Forbidden"}), 403
    role = ((request.get_json() or {}).get("role") or "").upper()
    if role not in ("ADMIN", "MANAGER", "TECH"):
        return jsonify({"error": "invalid role"}), 400
    u = User.query.get_or_404(user_id)
    u.role = role
    db.session.commit()
    return jsonify({"message": "role updated"}), 200

@admin_users_bp.put("/admin/users/<int:user_id>/status")
@jwt_required()
def admin_toggle_active(user_id):
    if not _require_admin():
        return jsonify({"error": "Forbidden"}), 403
    active = bool((request.get_json() or {}).get("is_active", True))
    u = User.query.get_or_404(user_id)
    u.is_active = active
    db.session.commit()
    return jsonify({"message": "status updated", "is_active": u.is_active}), 200

@admin_users_bp.post("/admin/users/<int:user_id>/reset-password")
@jwt_required()
def admin_reset_password(user_id):
    if not _require_admin():
        return jsonify({"error": "Forbidden"}), 403
    new_temp = (request.get_json() or {}).get("temp_password")
    if not new_temp:
        import secrets, string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        new_temp = "".join(secrets.choice(alphabet) for _ in range(12))
    u = User.query.get_or_404(user_id)
    u.password_hash = generate_password_hash(new_temp)
    u.must_change_password = True
    u.last_temp_password = new_temp       # ✅ persist latest temp
    db.session.commit()
    try:
        send_temp_password_email(u.email, u.name, new_temp)
    except Exception:
        pass
    return jsonify({
        "message": "password reset issued",
        "temp_password": new_temp,
        "user_id": u.id
    }), 200