# app/resources/assets.py
from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from flask_jwt_extended import jwt_required
from app.middlewares.rbac import roles_required
from app import db
from app.models import Asset

assets_bp = Blueprint("assets", __name__)

def dump_asset(a: Asset):
    return {
        "id": a.id,
        "name": a.name,
        "category": a.category,
        "location": a.location,
        "purchase_date": a.purchase_date.isoformat() if a.purchase_date else None,
        "warranty_end": a.warranty_end.isoformat() if a.warranty_end else None,
        "assigned_user_id": a.assigned_user_id,
        "qr_code_path": a.qr_code_path,
    }

@assets_bp.get("/")
@jwt_required()
def list_assets():
    q = Asset.query
    if location := request.args.get("location"):
        q = q.filter(Asset.location == location)
    if category := request.args.get("category"):
        q = q.filter(Asset.category == category)
    if assigned := request.args.get("assigned_user_id"):
        try:
            q = q.filter(Asset.assigned_user_id == int(assigned))
        except ValueError:
            return jsonify({"error": "assigned_user_id must be int"}), 400

    page = max(1, int(request.args.get("page", 1)))
    size = min(100, int(request.args.get("size", 20)))

    total = q.count()
    items = q.order_by(desc(Asset.updated_at)).offset((page - 1) * size).limit(size).all()
    return {"items": [dump_asset(a) for a in items], "total": total, "page": page, "size": size}

@assets_bp.post("/")
@jwt_required()
@roles_required("ADMIN", "MANAGER")
def create_asset():
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "name required"}), 400
    a = Asset(
        name=data["name"],
        category=data.get("category"),
        location=data.get("location"),
        assigned_user_id=data.get("assigned_user_id"),
        purchase_date=data.get("purchase_date"),
        warranty_end=data.get("warranty_end"),
    )
    db.session.add(a)
    db.session.commit()
    return {"id": a.id, "message": "created"}, 201

@assets_bp.put("/<int:asset_id>")
@jwt_required()
@roles_required("ADMIN", "MANAGER")
def update_asset(asset_id):
    a = Asset.query.get_or_404(asset_id)
    data = request.get_json() or {}
    for f in ["name", "category", "location", "purchase_date", "warranty_end", "assigned_user_id", "qr_code_path"]:
        if f in data:
            setattr(a, f, data[f])
    db.session.commit()
    return {"message": "updated"}

@assets_bp.delete("/<int:asset_id>")
@jwt_required()
@roles_required("ADMIN", "MANAGER")
def delete_asset(asset_id):
    a = Asset.query.get_or_404(asset_id)
    db.session.delete(a)
    db.session.commit()
    return {"message": "deleted"}