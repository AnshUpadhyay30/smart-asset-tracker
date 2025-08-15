from .. import db

class MaintenanceLog(db.Model):
    __tablename__ = "maintenance_logs"

    # 🔑 Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # 🔗 Foreign Key to Asset
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)

    # 🗓️ Maintenance date
    service_date = db.Column(db.Date, nullable=False)

    # 🧾 Log details
    description = db.Column(db.Text)
    parts_used = db.Column(db.String(255))
    cost = db.Column(db.Numeric(10, 2), default=0)
    attachment_path = db.Column(db.String(255))

    # 🔁 Calculated next service date
    next_service_due = db.Column(db.Date)

    # 👨‍🔧 Technician info
    technician_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # 🕒 Created timestamp
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # 📎 Relationships (NO duplicate backref)
    asset = db.relationship("Asset", backref="maintenance_logs")  # Creates asset.maintenance_logs automatically
    technician = db.relationship("User", backref="maintenance_jobs")  # Creates technician.maintenance_jobs