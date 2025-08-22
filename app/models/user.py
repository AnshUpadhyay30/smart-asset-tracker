# app/models/user.py
from .. import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # unique username (admin suggest/assign)
    username = db.Column(db.String(60), unique=True, nullable=True)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # RBAC
    role = db.Column(
        db.Enum("ADMIN", "MANAGER", "TECH", name="user_roles"),
        default="TECH",
        nullable=False
    )

    # enterprise flags
    is_active = db.Column(db.Boolean, default=True)              # can login?
    must_change_password = db.Column(db.Boolean, default=False)  # force reset on first login

    # ✅ admin UI ke liye: last issued temporary password (optional)
    last_temp_password = db.Column(db.String(128), nullable=True)

    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # reverse relation
    assets = db.relationship("Asset", backref="assigned_user", lazy=True)

    # helpers
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)