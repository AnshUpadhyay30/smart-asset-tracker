from flask import Blueprint, jsonify
from app.models import Asset, MaintenanceLog
from datetime import date
from sqlalchemy import extract, func
from app import db

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard-summary", methods=["GET"])
def dashboard_summary():
    try:
        total_assets = Asset.query.count()
        total_logs = MaintenanceLog.query.count()
        overdue_logs = MaintenanceLog.query.filter(MaintenanceLog.next_service_due < date.today()).count()

        # Monthly maintenance cost aggregation
        monthly_costs = (
            db.session.query(
                extract('month', MaintenanceLog.service_date).label('month'),
                func.sum(MaintenanceLog.cost).label('cost')
            )
            .group_by('month')
            .order_by('month')
            .all()
        )

        # Convert month number to name
        month_map = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_cost = [
            {"month": month_map[int(month) - 1], "cost": float(cost)} for month, cost in monthly_costs
        ]

        return jsonify({
            "total_assets": total_assets,
            "total_logs": total_logs,
            "overdue_logs": overdue_logs,
            "monthly_cost": monthly_cost
        })

    except Exception as e:
        print("❌ Dashboard summary error:", e)
        return jsonify({"error": "Internal Server Error"}), 500