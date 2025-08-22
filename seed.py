# seed.py
"""
Idempotent seeding for local/dev:
- Creates/updates 3 users (ADMIN / MANAGER / TECH)
- Creates/updates two assets
- Adds one sample maintenance log if missing
- Generates QR images if missing

Run:  python seed.py
"""

import datetime
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.user import User
from app.models.asset import Asset
from app.models.maintenance_log import MaintenanceLog

# try to import QR generator (optional)
try:
    from app.utils.qr_utils import generate_qr
except Exception:
    generate_qr = None

app = create_app()

def upsert_user(name: str, email: str, password: str, role: str) -> User:
    """Create or update a user with first-login flag on (so you can test reset)."""
    u = User.query.filter_by(email=email.lower()).first()
    if u:
        u.name = name
        u.role = role
        u.password_hash = generate_password_hash(password)
        if hasattr(u, "is_active"): u.is_active = True
        if hasattr(u, "must_change_password"): u.must_change_password = True
    else:
        kwargs = dict(
            name=name,
            email=email.lower(),
            role=role,
            password_hash=generate_password_hash(password),
        )
        # optional flags if model has them
        if hasattr(User, "is_active"): kwargs["is_active"] = True
        if hasattr(User, "must_change_password"): kwargs["must_change_password"] = True
        u = User(**kwargs)
        db.session.add(u)
    return u

def upsert_asset(name: str, **kwargs) -> Asset:
    a = Asset.query.filter_by(name=name).first()
    if a:
        for k, v in kwargs.items():
            setattr(a, k, v)
    else:
        a = Asset(name=name, **kwargs)
        db.session.add(a)
    return a

def ensure_qr(a: Asset):
    if not generate_qr:
        return
    if not getattr(a, "qr_code_path", None):
        try:
            a.qr_code_path = generate_qr(a.id, f"smartasset://asset/{a.id}")
        except TypeError:
            a.qr_code_path = generate_qr(a.id)

with app.app_context():
    # ---- Users ----
    admin   = upsert_user("Admin User",   "admin@example.com",   "Admin@123",   "ADMIN")
    manager = upsert_user("Manager User", "manager@example.com", "Manager@123", "MANAGER")
    tech    = upsert_user("Tech User",    "tech@example.com",    "Tech@123",    "TECH")
    db.session.commit()

    # ---- Assets ----
    a1 = upsert_asset(
        "Laptop A",
        category="Electronics",
        location="Delhi",
        purchase_date=datetime.date(2024, 5, 10),
        warranty_end=datetime.date(2026, 5, 10),
        frequency_days=180,
        assigned_user_id=manager.id,
    )
    a2 = upsert_asset(
        "Printer B",
        category="Office",
        location="Mumbai",
        purchase_date=datetime.date(2023, 3, 15),
        warranty_end=datetime.date(2025, 3, 15),
        frequency_days=90,
        assigned_user_id=tech.id,
    )

    # QR images if missing
    ensure_qr(a1)
    ensure_qr(a2)
    db.session.commit()

    # ---- Sample maintenance log (only once) ----
    if not MaintenanceLog.query.filter_by(description="Battery replaced").first():
        log = MaintenanceLog(
            asset_id=a1.id,
            service_date=datetime.date(2025, 1, 5),
            description="Battery replaced",
            parts_used="Battery",
            cost=5000.00,
            technician_id=tech.id,
        )
        db.session.add(log)
        db.session.commit()

    print("✅ Seed complete.")