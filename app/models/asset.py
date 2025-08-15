from .. import db

class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)

    # 📌 Basic info
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60))
    location = db.Column(db.String(100))

    # 📅 Dates
    purchase_date = db.Column(db.Date)
    warranty_end = db.Column(db.Date)

    # 🔁 Service frequency in days
    frequency_days = db.Column(db.Integer, default=180)  # ✅ Used to calculate next_service_due

    # 👤 Assigned to user
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # 📸 QR Code image path
    qr_code_path = db.Column(db.String(255))

    # 🕒 Timestamps
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.TIMESTAMP,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # 🔍 Useful indexes
    __table_args__ = (
        db.Index("idx_assets_category", "category"),
        db.Index("idx_assets_location", "location"),
        db.Index("idx_assets_warranty", "warranty_end"),
    )

    # 🔍 Latest log shortcut
    @property
    def latest_log(self):
        return sorted(self.maintenance_logs, key=lambda x: x.service_date, reverse=True)[0] if self.maintenance_logs else None