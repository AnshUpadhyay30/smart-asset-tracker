from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models import MaintenanceLog, Asset, User
from datetime import datetime, timedelta

maintenance_bp = Blueprint("maintenance", __name__)

# ✅ Reusable Role Checker
def has_role(required_role):
    def wrapper(fn):
        from functools import wraps
        @wraps(fn)
        def decorated(*args, **kwargs):
            claims = get_jwt()
            if claims["role"] != required_role:
                return jsonify({"error": "Forbidden: Insufficient role"}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper

# ✅ POST - TECH can add maintenance log with calculated next_service_due
@maintenance_bp.route("/assets/<int:asset_id>/maintenance", methods=["POST"])
@jwt_required()
@has_role("TECH")
def add_maintenance_log(asset_id):
    data = request.get_json()
    description = data.get("description")
    parts_used = data.get("parts_used")
    cost = data.get("cost", 0)
    attachment_path = data.get("attachment_path")

    # 🔄 Calculate next_service_due using asset's frequency_days
    asset = Asset.query.get_or_404(asset_id)
    service_date = datetime.utcnow().date()
    frequency_days = asset.frequency_days or 180  # default if None
    next_service_due = service_date + timedelta(days=frequency_days)

    technician_id = get_jwt_identity()

    new_log = MaintenanceLog(
        asset_id=asset_id,
        service_date=service_date,
        description=description,
        parts_used=parts_used,
        cost=cost,
        technician_id=technician_id,
        attachment_path=attachment_path,
        next_service_due=next_service_due
    )

    db.session.add(new_log)
    db.session.commit()

    return jsonify({
        "message": "Maintenance log added",
        "log_id": new_log.id,
        "next_service_due": next_service_due.isoformat()
    }), 201

# ✅ GET - Anyone can view logs for an asset
@maintenance_bp.route("/assets/<int:asset_id>/maintenance", methods=["GET"])
@jwt_required()
def get_logs(asset_id):
    logs = MaintenanceLog.query.filter_by(asset_id=asset_id).all()
    return jsonify([{
        "id": log.id,
        "description": log.description,
        "service_date": log.service_date.strftime("%Y-%m-%d"),
        "parts_used": log.parts_used,
        "cost": str(log.cost),
        "technician_id": log.technician_id,
        "attachment_path": log.attachment_path,
        "next_service_due": log.next_service_due.strftime("%Y-%m-%d") if log.next_service_due else None
    } for log in logs]), 200

# ✅ PUT - MANAGER can update a log
@maintenance_bp.route("/maintenance/<int:log_id>", methods=["PUT"])
@jwt_required()
@has_role("MANAGER")
def update_log(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    data = request.get_json()

    log.description = data.get("description", log.description)
    log.parts_used = data.get("parts_used", log.parts_used)
    log.cost = data.get("cost", log.cost)
    log.attachment_path = data.get("attachment_path", log.attachment_path)

    # Update next_service_due if provided
    if "next_service_due" in data:
        log.next_service_due = datetime.strptime(data["next_service_due"], "%Y-%m-%d").date()

    db.session.commit()
    return jsonify({"message": "Log updated"}), 200

# ✅ DELETE - ADMIN can delete a log
@maintenance_bp.route("/maintenance/<int:log_id>", methods=["DELETE"])
@jwt_required()
@has_role("ADMIN")
def delete_log(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({"message": "Log deleted"}), 200