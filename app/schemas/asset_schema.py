# /app/schemas/asset_schema.py

from marshmallow import Schema, fields, validate

class AssetSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    category = fields.Str(required=True)
    location = fields.Str(required=True)
    purchase_date = fields.Date(required=True)
    condition = fields.Str(validate=validate.OneOf(["Good", "Fair", "Poor"]))
    assigned_user_id = fields.Int(allow_none=True)
    qr_code_path = fields.Str(dump_only=True)  # ✅ Add this line
    created_at = fields.DateTime(dump_only=True)

# Register schemas
asset_schema = AssetSchema()
assets_schema = AssetSchema(many=True)