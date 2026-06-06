"""Review log model (审核记录表)."""

from app import db


class ReviewLog(db.Model):
    """Review log entry for AI or human review actions."""

    __tablename__ = "review_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    registration_id = db.Column(db.Integer, db.ForeignKey("registrations.id"))
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    review_type = db.Column(db.String(20), nullable=False)
    result = db.Column(db.String(20), nullable=False)
    comment = db.Column(db.Text)
    score = db.Column(db.Numeric(5, 2))
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    registration = db.relationship(
        "Registration",
        back_populates="review_logs",
    )
    reviewer = db.relationship(
        "User",
        back_populates="review_logs",
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewLog registration={self.registration_id} "
            f"type={self.review_type} result={self.result}>"
        )
