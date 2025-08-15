from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from app.models import Asset, MaintenanceLog
from app.schemas.asset_schema import asset_schema, assets_schema
from app.utils.qr_utils import generate_qr  # ✅ QR generator
from datetime import datetime

# 🔧 Blueprint for asset-related routes
asset_bp = Blueprint("asset_routes", __name__)

# 🔐 Role check decorator
def has_role(*roles):
    def wrapper(fn):
        from functools import wraps
        @wraps(fn)
        def decorated(*args, **kwargs):
            claims = get_jwt()
            if claims["role"] not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper

# ✅ GET all assets with optional filters and pagination
@asset_bp.route("", methods=["GET"])
@jwt_required()
def list_assets():
    role = get_jwt().get("role")
    if role not in ["ADMIN", "MANAGER", "TECH"]:
        return jsonify({"error": "Forbidden"}), 403

    query = Asset.query

    # 🔍 Apply optional filters
    if location := request.args.get("location"):
        query = query.filter_by(location=location)
    if category := request.args.get("category"):
        query = query.filter_by(category=category)
    if assigned_user := request.args.get("assigned_user"):
        query = query.filter_by(assigned_user_id=assigned_user)

    # 📃 Pagination
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        "items": assets_schema.dump(paginated.items),
        "total": paginated.total,
        "page": page,
        "pages": paginated.pages
    }), 200

# ✅ POST - Create a new asset
@asset_bp.route("", methods=["POST"])
@jwt_required()
@has_role("ADMIN", "MANAGER")
def create_asset():
    data = request.get_json()
    errors = asset_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    asset = Asset(**data)
    db.session.add(asset)
    db.session.commit()

    # 📸 Generate QR code after creating asset
    asset.qr_code_path = generate_qr(asset.id)
    db.session.commit()

    return jsonify(asset_schema.dump(asset)), 201

# ✅ PUT - Update an asset
@asset_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@has_role("ADMIN", "MANAGER")
def update_asset(id):
    asset = Asset.query.get_or_404(id)
    data = request.get_json()
    errors = asset_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400

    # 🛠 Dynamically update fields
    for key, value in data.items():
        setattr(asset, key, value)

    db.session.commit()

    # 🔁 Regenerate QR code
    asset.qr_code_path = generate_qr(asset.id)
    db.session.commit()

    return jsonify(asset_schema.dump(asset)), 200

# ✅ DELETE - Remove asset
@asset_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@has_role("ADMIN")
def delete_asset(id):
    asset = Asset.query.get_or_404(id)
    db.session.delete(asset)
    db.session.commit()
    return jsonify({"message": "Asset deleted"}), 200

# ✅ GET - Asset detail by ID (including QR path)
@asset_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_asset(id):
    asset = Asset.query.get_or_404(id)
    return jsonify(asset_schema.dump(asset)), 200

# ✅ GET - Latest maintenance log for specific asset
@asset_bp.route("/<int:asset_id>/latest-log", methods=["GET"])
@jwt_required()
def get_latest_log(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    latest = asset.latest_log
    if not latest:
        return jsonify({"message": "No logs yet"}), 404

    return jsonify({
        "id": latest.id,
        "description": latest.description,
        "service_date": latest.service_date.strftime("%Y-%m-%d"),
        "next_service_due": latest.next_service_due.strftime("%Y-%m-%d") if latest.next_service_due else None
    }), 200

# ✅ GET - List of assets due or overdue for maintenance
@asset_bp.route("/due", methods=["GET"])
@jwt_required()
def get_due_assets():
    today = datetime.utcnow().date()

    # 📦 Join Asset + MaintenanceLog to find due/overdue assets
    due_assets = Asset.query.join(MaintenanceLog).filter(
        MaintenanceLog.next_service_due <= today
    ).all()

    return jsonify([
        {
            "id": asset.id,
            "name": asset.name,
            "category": asset.category,
            "location": asset.location
        }
        for asset in due_assets
    ]), 200