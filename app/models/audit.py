from .. import db

class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    entity = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    action = db.Column(db.String(20))  # CREATE / UPDATE / DELETE / LOGIN
    changes = db.Column(db.JSON)
    at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # Relationship
    user = db.relationship("User", backref="audit_logs")