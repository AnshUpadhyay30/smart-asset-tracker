# /app/resources/report_routes.py

from flask import Blueprint, jsonify, request, current_app, send_file
from flask_jwt_extended import jwt_required
from app import db
from app.models.maintenance_log import MaintenanceLog
from app.models.asset import Asset
from sqlalchemy import extract, func
from datetime import datetime, timedelta
import csv
import io

report_bp = Blueprint("reports", __name__)

# ───────────────────────────────────────────────────────────────
# ✅ 1. Monthly Maintenance Cost Report (Last 12 Months)
# ───────────────────────────────────────────────────────────────
@report_bp.route("/reports/monthly-cost", methods=["GET"])
@jwt_required()
def monthly_cost():
    """
    Returns total maintenance cost per month for the past 12 months.
    Grouped by year and month.
    """
    today = datetime.today()
    one_year_ago = today.replace(year=today.year - 1)

    results = db.session.query(
        extract("year", MaintenanceLog.service_date).label("year"),
        extract("month", MaintenanceLog.service_date).label("month"),
        func.sum(MaintenanceLog.cost).label("total_cost")
    ).filter(
        MaintenanceLog.service_date >= one_year_ago
    ).group_by("year", "month").order_by("year", "month").all()

    data = [
        {
            "year": int(r.year),
            "month": int(r.month),
            "total_cost": float(r.total_cost)
        } for r in results
    ]
    return jsonify(data)

# ───────────────────────────────────────────────────────────────
# ✅ 2. Warranty Expiring Soon Report
# ───────────────────────────────────────────────────────────────
@report_bp.route("/reports/warranty-expiring", methods=["GET"])
@jwt_required()
def warranty_expiring():
    """
    Returns list of assets whose warranty ends within the next X days.
    Default is 30 days.
    """
    try:
        days = int(request.args.get("days", 30))
    except ValueError:
        return jsonify({"error": "Invalid 'days' parameter"}), 400

    today = datetime.today().date()
    deadline = today + timedelta(days=days)

    assets = Asset.query.filter(
        Asset.warranty_end != None,
        Asset.warranty_end >= today,
        Asset.warranty_end <= deadline
    ).all()

    return jsonify([
        {
            "id": a.id,
            "name": a.name,
            "category": a.category,
            "warranty_end": a.warranty_end.strftime("%Y-%m-%d")
        } for a in assets
    ])

# ───────────────────────────────────────────────────────────────
# ✅ 3a. Export Assets to CSV
# ───────────────────────────────────────────────────────────────
@report_bp.route("/reports/assets/export", methods=["GET"])
@jwt_required()
def export_assets_csv():
    """
    Returns all assets as a downloadable CSV file.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "Name", "Category", "Location", "Purchase Date", "Warranty End", "Frequency Days"])

    for asset in Asset.query.all():
        writer.writerow([
            asset.id,
            asset.name,
            asset.category,
            asset.location,
            asset.purchase_date.strftime("%Y-%m-%d") if asset.purchase_date else "",
            asset.warranty_end.strftime("%Y-%m-%d") if asset.warranty_end else "",
            asset.frequency_days or 0
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="assets.csv"
    )

# ───────────────────────────────────────────────────────────────
# ✅ 3b. Export Maintenance Logs to CSV
# ───────────────────────────────────────────────────────────────
@report_bp.route("/reports/logs/export", methods=["GET"])
@jwt_required()
def export_logs_csv():
    """
    Returns all maintenance logs as a downloadable CSV file.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Asset ID", "Service Date", "Description",
        "Parts Used", "Cost", "Technician ID", "Next Service Due", "Created At"
    ])

    for log in MaintenanceLog.query.all():
        writer.writerow([
            log.id,
            log.asset_id,
            log.service_date.strftime("%Y-%m-%d") if log.service_date else "",
            log.description or "",
            log.parts_used or "",
            float(log.cost) if log.cost else 0.0,
            log.technician_id or "",
            log.next_service_due.strftime("%Y-%m-%d") if log.next_service_due else "",
            log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else ""
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="maintenance_logs.csv"
    )