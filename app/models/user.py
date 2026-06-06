"""User model for admin accounts."""

from app import db


class User(db.Model):
    """Admin user account model."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="admin")
    name = db.Column(db.String(50))
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    review_logs = db.relationship(
        "ReviewLog",
        back_populates="reviewer",
        lazy="dynamic",
    )
    registrations_reviewed = db.relationship(
        "Registration",
        back_populates="reviewer",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
