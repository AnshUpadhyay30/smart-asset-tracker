# app/routes/asset_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from marshmallow import ValidationError
from app import db
from app.models import Asset, MaintenanceLog
from app.schemas.asset_schema import asset_schema, assets_schema
from app.utils.qr_utils import generate_qr
from datetime import datetime, date
from sqlalchemy import func, text
import os

asset_bp = Blueprint("asset_routes", __name__)

# ─────────────────────────────────────────────────────────
# RBAC helper (role check)
# ─────────────────────────────────────────────────────────
def has_role(*roles):
    def wrapper(fn):
        from functools import wraps
        @wraps(fn)
        def decorated(*args, **kwargs):
            claims = get_jwt() or {}
            if claims.get("role") not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper

# Absolute URL banana (QR/file ke liye)
def _upload_url(filename: str | None):
    if not filename:
        return None
    fname = os.path.basename(filename)
    base = (current_app.config.get("PUBLIC_BASE_URL") or "").rstrip("/")
    return f"{base}/api/uploads/{fname}"

# ─────────────────────────────────────────────────────────
# LIST (filters + pagination)
# ─────────────────────────────────────────────────────────
@asset_bp.route("", methods=["GET"])
@jwt_required()
def list_assets():
    claims = get_jwt() or {}
    role = claims.get("role")
    user_id = claims.get("sub")

    if role not in ["ADMIN", "MANAGER", "TECH"]:
        return jsonify({"error": "Forbidden"}), 403

    q = Asset.query
    if role == "TECH":
        q = q.filter_by(assigned_user_id=user_id)

    if location := request.args.get("location"):
        q = q.filter_by(location=location)
    if category := request.args.get("category"):
        q = q.filter_by(category=category)
    if assigned_user := request.args.get("assigned_user"):
        q = q.filter_by(assigned_user_id=assigned_user)

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    paginated = q.paginate(page=page, per_page=limit, error_out=False)

    items = assets_schema.dump(paginated.items)
    for it in items:
        it["qr_url"] = _upload_url(it.get("qr_code_path"))

    return jsonify({
        "items": items,
        "total": paginated.total,
        "page": page,
        "pages": paginated.pages
    }), 200

# ─────────────────────────────────────────────────────────
# CREATE (Marshmallow .load → string date -> date)
# ─────────────────────────────────────────────────────────
@asset_bp.route("", methods=["POST"])
@jwt_required()
@has_role("ADMIN", "MANAGER")
def create_asset():
    raw = request.get_json() or {}
    try:
        data = asset_schema.load(raw)  # ✅ validate + deserialize
    except ValidationError as ve:
        return jsonify({"errors": ve.messages}), 400

    asset = Asset(**data)
    db.session.add(asset)
    db.session.commit()

    # QR generate
    try:
        asset.qr_code_path = generate_qr(asset.id, f"smartasset://asset/{asset.id}")
    except TypeError:
        asset.qr_code_path = generate_qr(asset.id)
    db.session.commit()

    out = asset_schema.dump(asset)
    out["qr_url"] = _upload_url(asset.qr_code_path)
    return jsonify(out), 201

# ─────────────────────────────────────────────────────────
# UPDATE (partial=True)
# ─────────────────────────────────────────────────────────
@asset_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@has_role("ADMIN", "MANAGER")
def update_asset(id):
    asset = Asset.query.get_or_404(id)
    raw = request.get_json() or {}
    try:
        data = asset_schema.load(raw, partial=True)
    except ValidationError as ve:
        return jsonify({"errors": ve.messages}), 400

    for k, v in data.items():
        setattr(asset, k, v)
    db.session.commit()

    # QR refresh (optional but consistent)
    try:
        asset.qr_code_path = generate_qr(asset.id, f"smartasset://asset/{asset.id}")
    except TypeError:
        asset.qr_code_path = generate_qr(asset.id)
    db.session.commit()

    out = asset_schema.dump(asset)
    out["qr_url"] = _upload_url(asset.qr_code_path)
    return jsonify(out), 200

# ─────────────────────────────────────────────────────────────────────
# DELETE (pehle maintenance logs delete → phir asset)  FK error se bachao
# ─────────────────────────────────────────────────────────────────────
@asset_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@has_role("ADMIN")
def delete_asset(id):
    asset = Asset.query.get_or_404(id)

    # Child logs bulk delete (fast + no FK issues even w/o DB CASCADE)
    MaintenanceLog.query.filter_by(asset_id=id).delete(synchronize_session=False)

    db.session.delete(asset)
    db.session.commit()
    return jsonify({"message": "Asset deleted"}), 200

# ─────────────────────────────────────────────────────────
# GET by id
# ─────────────────────────────────────────────────────────
@asset_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_asset(id):
    asset = Asset.query.get_or_404(id)
    out = asset_schema.dump(asset)
    out["qr_url"] = _upload_url(asset.qr_code_path)
    return jsonify(out), 200

# (latest-log, due, dashboard-summary, /:id/qr → same as before)