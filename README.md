🛠️ Smart Asset & Maintenance Tracker

A full-stack app to manage company assets, maintenance schedules, warranties, QR scan, reports — with secure auth & role-based access.
Built with Flask + MySQL (API) and Angular (Web).


🚀 Features
	•	🔐 JWT Auth + RBAC: ADMIN, MANAGER, TECH
	•	🧾 Assets CRUD with QR code per asset
	•	🛠️ Maintenance Logs (auto “next due” calc)
	•	📆 Warranty & Cost Reports (monthly)
	•	📤 Secure Uploads (invoices/images/PDF)
	•	🧪 QR Public View for assets (read-only)
	•	📊 Audit Trail (who did what, when)
	•	📎 CSV Export (assets/logs, users)
	•	👥 Admin: Users (create/bulk import, roles, enable/disable, temp   password reset & show)

🧰 Tech Stack

Layer
Tech
Backend
Python (Flask), SQLAlchemy, Flask-Migrate
Database
MySQL
Auth
JWT (flask-jwt-extended)
QR Codes
qrcode
Reports
SQL + Pandas/CSV
Frontend
Angular 17 + Angular Material


📂 Monorepo Structure


smart-asset/
├─ app/                        # Flask app
│  ├─ models/                  # User, Asset, MaintenanceLog, AuditLog...
│  ├─ resources/               # REST endpoints (auth, assets, maintenance, admin/users, reports, uploads, qr_public)
│  ├─ utils/                   # mailer, qr helpers, file utils
│  ├─ __init__.py              # app factory + DB/JWT init
│  └─ config.py                # configs
├─ migrations/                 # Alembic/Flask-Migrate history
├─ static/qr_codes/            # generated QR PNGs
├─ uploads/                    # uploaded files (gitignored)
├─ web/                        # Angular app
│  ├─ src/app/                 # components/pages/services/layout
│  └─ src/environments/        # Angular env files
├─ .env                        # backend env (gitignored)
├─ requirements.txt
└─ README.md


✅ Role Access Matrix

Action/Area
TECH
MANAGER
ADMIN
Login / View Dashboard
✅
✅
✅
Assets list/detail
✅
✅
✅
Create/Edit Assets
❌
✅
✅
Maintenance logs
✅
✅
✅
Reports
❌
✅
✅
Manage Users
❌
❌
✅


🔐 Authentication
	•	POST /api/auth/login → JWT
	•	Use header:
Authorization: Bearer <token>

Force password change: backend can set must_change_password=true after admin issues a temp password.


👥 Admin → Users (important)
	•	Create single/bulk (CSV: name,email,role,username)
	•	Toggle active / change roles
	•	Reset password returns a temp password (shown in UI “Temp Password” column for the current admin session; also stored in DB column last_temp_password if enabled).
	•	Export users CSV (includes any session-known temp passwords).

Security note: Temp passwords are only surfaced to admins. Users must change password at first login.

📈 Reports (examples)
	•	GET /api/reports/monthly-cost — last 12 months cost
	•	GET /api/reports/warranty-expiring?days=30
	•	GET /api/reports/assets/export — CSV
	•	GET /api/reports/logs/export — CSV

📎 Uploads
	•	POST /api/upload — multipart with JWT
	•	GET /api/uploads/<filename> — serve files


🔳 QR Public
	•	GET /api/qr/<asset_id> — read-only public asset info (configurable)


⚙️ Backend — Local Setup
	1.	Clone

    git clone https://github.com/AnshUpadhyay30/smart-asset-tracker.git
cd smart-asset

	2.	Virtualenv

   python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

	3.	Install deps

pip install -r requirements.txt

	4.	.env (create in project root)

    FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=change_me
JWT_SECRET_KEY=super_secret_change_me

DB_USER=root
DB_PASS=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=smart_asset

PUBLIC_BASE_URL=http://localhost:5000

	5.	DB migrate

    flask db init    # if fresh project
flask db migrate
flask db upgrade

	6.	Run

    flask run
# API → http://localhost:5000

🌐 Frontend (Angular) — Local Setup
	1.	Go to web/, install deps:

   cd web
npm install

2.	Environment (web/src/environments/environment.ts already points to backend). If needed:
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000'
};

	3.	Run dev

    npm start
# or
ng serve --open
# App → http://localhost:4200


🧪 Sample Users
Role
Email
Password
ADMIN
admin@example.com
admin123
MANAGER
manager@example.com
manager123
TECH
tech@example.com
tech123

📤 CSV Import (Users)

Header:

name,email,role,username

Sample:

Rohit,rohit@example.com,MANAGER,rohit.ch
Priya,priya@example.com,TECH,

🏭 Production build (Angular)
cd web
npm run build
# output in web/dist/...



🧯 Troubleshooting
	•	Unknown column 'users.last_temp_password'
Run the SQL:

ALTER TABLE `users`
  ADD COLUMN `last_temp_password` VARCHAR(128) NULL
  AFTER `must_change_password`;

  Then restart Flask.

	•	CORS issues → ensure backend CORS enabled for http://localhost:4200
	•	JWT 401 → confirm Authorization: Bearer <token>

🙏 Credits

Built with 💙 by Ansh Upadhyay — Python, Flask, Angular.

📄 License

MIT