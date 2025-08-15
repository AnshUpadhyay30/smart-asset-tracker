# 🛠️ Smart Asset & Maintenance Tracker

A full-stack application to manage company assets, schedule maintenance, and track warranties with QR code integration, secure file uploads, and audit logging.

## 🚀 Features

- 🔐 **JWT Authentication** with role-based access (`ADMIN`, `MANAGER`, `TECH`)
- 🧾 **Asset Management** (Create, Read, Update, Delete)
- 🛠️ **Maintenance Logs** with next due service calculation
- 📆 **Warranty Expiry & Cost Reports** (monthly)
- 📤 **Secure File Uploads** for invoices, images, PDFs
- 📊 **Audit Trail** to log who did what and when
- 📎 **CSV Export** for assets and logs
- 📱 **QR Code Generation** for each asset

---

## 🧰 Tech Stack

| Layer       | Technology          |
|-------------|---------------------|
| Backend     | Python, Flask       |
| Database    | MySQL               |
| Auth        | JWT (Flask-JWT-Extended) |
| ORM         | SQLAlchemy          |
| Migrations  | Flask-Migrate       |
| File Upload | Flask + Secure Utils |
| Reports     | Pandas, CSV, SQL    |
| QR Codes    | Python `qrcode`     |

---

## 📂 Folder Structure (Backend)

smart-asset/
├── app/
│   ├── models/             # DB Models: User, Asset, MaintenanceLog, AuditLog
│   ├── resources/          # Routes (auth, asset, maintenance, uploads, reports)
│   ├── routes/             # Clean modular routes
│   ├── utils/              # QR code & file helpers
│   ├── config.py           # Environment config
│   ├── init.py         # App factory
├── uploads/                # Uploaded files (images, bills, etc)
├── static/qr_codes/        # QR images for assets
├── migrations/             # DB migration history
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── README.md               # You are here 👋

---

## ✅ Role-based Access

| Role     | Access Allowed                                        |
|----------|--------------------------------------------------------|
| TECH     | Add/View maintenance logs, upload files               |
| MANAGER  | Edit assets, view reports                             |
| ADMIN    | Full access (delete, view audit logs, manage users)   |

---

## 🔐 Authentication

- `/api/auth/register` — Register user
- `/api/auth/login` — Login and receive JWT token

Include token in headers:  
Authorization: Bearer <your_token>

---

## 📈 Reports

- `/api/reports/monthly-cost` — Monthly maintenance cost (last 12 months)
- `/api/reports/warranty-expiring?days=30` — Warranty expiry within next 30 days
- `/api/reports/assets/export` — Download assets as CSV
- `/api/reports/logs/export` — Download logs as CSV

---

## 📎 Uploads

- `/api/upload` — Upload file (with token, via `multipart/form-data`)
- `/api/uploads/<filename>` — Download/view uploaded file

---

## 📦 Setup Instructions (Local)

1. Clone the repo:
```bash
git clone https://github.com/yourusername/smart-asset.git
cd smart-asset

2.	Create virtual environment:

python -m venv .venv
source .venv/bin/activate

3.	Install dependencies:

pip install -r requirements.txt

4.	Set environment variables in .env:

JWT_SECRET_KEY=your_jwt_secret
DB_USER=root
DB_PASS=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=smart_asset
PUBLIC_BASE_URL=http://localhost:5000

5.	Initialize database:

flask db init
flask db migrate
flask db upgrade

6.	Run the app:

flask run

🧪 Sample Test Accounts:

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

🙏 Credits

Built with 💙 by Ansh Upadhyay using Python, Flask, and passion for real-world problem solving.


📸 Screenshots

Add screenshots of your frontend (Angular) or API testing (Postman/cURL) here.


📄 License

MIT License
