"""Operation log model for audit trail."""

from app import db


class OperationLog(db.Model):
    """Operation log entry for auditing critical actions."""

    __tablename__ = "operation_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    user = db.relationship(
        "User",
        backref="operation_logs",
        lazy="joined",
    )
    student = db.relationship(
        "Student",
        backref="operation_logs",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<OperationLog {self.action} {self.target_type}={self.target_id}>"
