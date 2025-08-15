from marshmallow import Schema, fields

class MaintenanceLogSchema(Schema):
    id = fields.Int(dump_only=True)
    asset_id = fields.Int(required=True)
    service_date = fields.Date(required=True)
    description = fields.Str()
    parts_used = fields.Str()
    cost = fields.Float()
    technician_id = fields.Int()
    attachment_path = fields.Str()
    next_service_due = fields.Date(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

# Schema objects
maintenance_log_schema = MaintenanceLogSchema()
maintenance_logs_schema = MaintenanceLogSchema(many=True)