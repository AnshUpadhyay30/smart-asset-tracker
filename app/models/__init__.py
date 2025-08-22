# app/models/__init__.py
from .. import db

# Re-export models here (no model definitions in this file)
from .user import User
from .asset import Asset
from .maintenance_log import MaintenanceLog
from .audit import AuditLog

__all__ = ["User", "Asset", "MaintenanceLog", "AuditLog"]