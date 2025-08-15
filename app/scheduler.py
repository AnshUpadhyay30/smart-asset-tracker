# app/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
from datetime import datetime
from app.models.maintenance_log import MaintenanceLog
from app import db
import pytz

# 🔔 Shared function: sends daily maintenance due/overdue summary (simulates email)
def send_due_summary():
    """
    Query all due or overdue maintenance logs for today,
    generate a summary, and log it (console/email stub).
    """
    today = datetime.now(pytz.timezone("Asia/Kolkata")).date()

    # ⚙️ Query all maintenance logs that are due today or overdue
    due_logs = MaintenanceLog.query.filter(
        MaintenanceLog.next_service_due <= today
    ).all()

    # ✅ If no logs are due or overdue, log and exit
    if not due_logs:
        current_app.logger.info("✅ No due or overdue maintenance logs today.")
        return

    # 🧾 Build the summary report
    summary = f"🔔 {len(due_logs)} maintenance logs due/overdue:\n"
    for log in due_logs:
        summary += (
            f"• Asset ID: {log.asset_id} | "
            f"Due on: {log.next_service_due} | "
            f"Description: {log.description}\n"
        )

    # 🪵 Log the summary (can be replaced with email logic later)
    current_app.logger.info("\n📬 DAILY MAINTENANCE SUMMARY\n" + summary)
    current_app.logger.info("📨 Maintenance summary printed (stubbed email).")

# 🕒 Register the daily job to run at 6 AM IST
def start_scheduler(app):
    """
    Starts the background scheduler if ENABLE_SCHEDULER is True in config.
    Uses a cron job to run daily at 6 AM IST.
    """
    if not app.config.get("ENABLE_SCHEDULER", False):
        app.logger.info("⏳ Scheduler is disabled via config.")
        return

    # 🧠 APScheduler with timezone awareness
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Kolkata"))

    # 🔁 Cron job: runs daily at 6 AM IST
    @scheduler.scheduled_job(CronTrigger(hour=6, minute=0))
    def daily_summary_job():
        with app.app_context():
            send_due_summary()

    # 🚀 Start the scheduler
    scheduler.start()
    app.logger.info("✅ Scheduler started (Daily 6 AM IST).")