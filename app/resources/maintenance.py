# app/resources/maintenance.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models import MaintenanceLog, Asset
from datetime import datetime, timedelta

maintenance_bp = Blueprint("maintenance", __name__)

# ─────────────────────────────────────────────────────────
# Role helper (multi-role)
# ─────────────────────────────────────────────────────────
def roles_required(*roles):
    """
    Allow only given roles. Example:
    @roles_required("ADMIN", "MANAGER", "TECH")
    """
    def wrapper(fn):
        from functools import wraps
        @wraps(fn)
        def decorated(*args, **kwargs):
            claims = get_jwt() or {}
            role = claims.get("role")
            if role not in roles:
                return jsonify({"error": "Forbidden: Insufficient role"}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper

def _current_user_id() -> int:
    """
    JWT identity in our app is stored as string; convert to int.
    """
    return int(get_jwt_identity())

# ─────────────────────────────────────────────────────────
# POST: Create maintenance log
#   - ADMIN / MANAGER: any asset
#   - TECH: only for assets assigned to them
#   - next_service_due auto-calc if not provided
# Body example (Angular dialog):
# {
#   "description": "Fan cleaned",
#   "parts_used": "Brush",
#   "cost": 200,
#   "service_date": "2025-08-17",          # YYYY-MM-DD
#   "next_service_due": "2026-02-13"       # (optional)
# }
# ─────────────────────────────────────────────────────────
@maintenance_bp.route("/assets/<int:asset_id>/maintenance", methods=["POST"])
@jwt_required()
@roles_required("ADMIN", "MANAGER", "TECH")
def add_maintenance_log(asset_id):
    data = request.get_json() or {}

    # ensure asset exists
    asset = Asset.query.get_or_404(asset_id)

    # role & user
    claims = get_jwt() or {}
    role = claims.get("role")
    user_id = _current_user_id()

    # TECH can only operate on their assigned assets
    if role == "TECH" and asset.assigned_user_id != user_id:
        return jsonify({"error": "Forbidden: Asset not assigned to you"}), 403

    # normalize
    description = (data.get("description") or "").strip()
    parts_used  = (data.get("parts_used")  or "").strip()
    cost = float(data.get("cost") or 0)

    # service_date: accept from UI (YYYY-MM-DD) or default to today UTC
    if data.get("service_date"):
        try:
            service_date = datetime.strptime(data["service_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid service_date format, expected YYYY-MM-DD"}), 400
    else:
        service_date = datetime.utcnow().date()

    # next_service_due: provided or auto-calc by asset.frequency_days (default 180)
    if data.get("next_service_due"):
        try:
            next_service_due = datetime.strptime(data["next_service_due"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid next_service_due format, expected YYYY-MM-DD"}), 400
    else:
        freq = asset.frequency_days or 180
        next_service_due = service_date + timedelta(days=freq)

    new_log = MaintenanceLog(
        asset_id=asset_id,
        service_date=service_date,
        description=description,
        parts_used=parts_used,
        cost=cost,
        technician_id=user_id,
        attachment_path=data.get("attachment_path"),
        next_service_due=next_service_due
    )

    db.session.add(new_log)
    db.session.commit()

    return jsonify({
        "message": "Maintenance log added",
        "log": {
            "id": new_log.id,
            "asset_id": asset_id,
            "service_date": new_log.service_date.strftime("%Y-%m-%d") if new_log.service_date else None,
            "description": new_log.description,
            "parts_used": new_log.parts_used,
            "cost": float(new_log.cost or 0),
            "technician_id": new_log.technician_id,
            "attachment_path": new_log.attachment_path,
            "next_service_due": new_log.next_service_due.strftime("%Y-%m-%d") if new_log.next_service_due else None
        }
    }), 201

# ─────────────────────────────────────────────────────────
# GET: List logs for asset (all authenticated roles)
# ─────────────────────────────────────────────────────────
@maintenance_bp.route("/assets/<int:asset_id>/maintenance", methods=["GET"])
@jwt_required()
def get_logs(asset_id):
    # ensure asset exists
    Asset.query.get_or_404(asset_id)

    logs = (
        MaintenanceLog.query
        .filter_by(asset_id=asset_id)
        .order_by(MaintenanceLog.service_date.desc())
        .all()
    )

    return jsonify([
        {
            "id": log.id,
            "description": log.description,
            "service_date": log.service_date.strftime("%Y-%m-%d") if log.service_date else None,
            "parts_used": log.parts_used,
            "cost": float(log.cost or 0),
            "technician_id": log.technician_id,
            "attachment_path": log.attachment_path,
            "next_service_due": log.next_service_due.strftime("%Y-%m-%d") if log.next_service_due else None
        }
        for log in logs
    ]), 200

# ─────────────────────────────────────────────────────────
# PUT: Update a log
#   - ADMIN / MANAGER: can update any
#   - TECH: can update only their own log & assigned asset
# ─────────────────────────────────────────────────────────
@maintenance_bp.route("/maintenance/<int:log_id>", methods=["PUT"])
@jwt_required()
@roles_required("ADMIN", "MANAGER", "TECH")
def update_log(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    asset = Asset.query.get_or_404(log.asset_id)

    claims = get_jwt() or {}
    role = claims.get("role")
    user_id = _current_user_id()

    if role == "TECH":
        if log.technician_id != user_id or asset.assigned_user_id != user_id:
            return jsonify({"error": "Forbidden: Not allowed to update this log"}), 403

    data = request.get_json() or {}

    if "description" in data:
        log.description = (data["description"] or "").strip()
    if "parts_used" in data:
        log.parts_used = (data["parts_used"] or "").strip()
    if "cost" in data:
        log.cost = float(data["cost"] or 0)
    if "attachment_path" in data:
        log.attachment_path = data["attachment_path"]

    if "service_date" in data and data["service_date"]:
        try:
            log.service_date = datetime.strptime(data["service_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid service_date format, expected YYYY-MM-DD"}), 400

    if "next_service_due" in data and data["next_service_due"]:
        try:
            log.next_service_due = datetime.strptime(data["next_service_due"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid next_service_due format, expected YYYY-MM-DD"}), 400

    db.session.commit()
    return jsonify({"message": "Log updated"}), 200

# ─────────────────────────────────────────────────────────
# DELETE: ADMIN only
# ─────────────────────────────────────────────────────────
@maintenance_bp.route("/maintenance/<int:log_id>", methods=["DELETE"])
@jwt_required()
@roles_required("ADMIN")
def delete_log(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({"message": "Log deleted"}), 200