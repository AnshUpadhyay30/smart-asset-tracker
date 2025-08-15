# seed.py
from app import create_app, db
from app.models.user import User
from app.models.asset import Asset
from app.models.maintenance_log import MaintenanceLog
from werkzeug.security import generate_password_hash
import datetime

app = create_app()
app.app_context().push()

# Users
u1 = User(name="Admin User", email="admin@example.com",
          password_hash=generate_password_hash("admin123"), role="ADMIN")
u2 = User(name="Manager User", email="manager@example.com",
          password_hash=generate_password_hash("manager123"), role="MANAGER")
u3 = User(name="Tech User", email="tech@example.com",
          password_hash=generate_password_hash("tech123"), role="TECH")

db.session.add_all([u1, u2, u3])
db.session.commit()

# Assets
a1 = Asset(name="Laptop A", category="Electronics", location="Delhi",
           purchase_date=datetime.date(2024, 5, 10),
           warranty_end=datetime.date(2026, 5, 10),
           assigned_user_id=u2.id)
a2 = Asset(name="Printer B", category="Office", location="Mumbai",
           purchase_date=datetime.date(2023, 3, 15),
           warranty_end=datetime.date(2025, 3, 15),
           assigned_user_id=u3.id)

db.session.add_all([a1, a2])
db.session.commit()

# Maintenance Logs
m1 = MaintenanceLog(asset_id=a1.id, service_date=datetime.date(2025, 1, 5),
                     description="Battery replaced", parts_used="Battery",
                     cost=5000.00, technician_id=u3.id)

db.session.add(m1)
db.session.commit()

print("✅ Seed data inserted successfully!")