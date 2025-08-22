# app/models/maintenance_log.py
from .. import db

class MaintenanceLog(db.Model):
    __tablename__ = "maintenance_logs"

    id = db.Column(db.Integer, primary_key=True)

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False
    )

    service_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    parts_used = db.Column(db.String(255))
    cost = db.Column(db.Numeric(10, 2), default=0)
    attachment_path = db.Column(db.String(255))
    next_service_due = db.Column(db.Date)
    technician_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    asset = db.relationship(
        "Asset",
        backref=db.backref("maintenance_logs", cascade="all, delete-orphan"),
        passive_deletes=True
    )
    technician = db.relationship("User", backref="maintenance_jobs")