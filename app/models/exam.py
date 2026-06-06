"""Exam model."""

from app import db


class Exam(db.Model):
    """Exam information model."""

    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cert_type_id = db.Column(db.Integer, db.ForeignKey("cert_types.id"))
    exam_name = db.Column(db.String(200), nullable=False)
    exam_date = db.Column(db.Date)
    registration_start = db.Column(db.Date)
    registration_end = db.Column(db.Date)
    exam_location = db.Column(db.String(200))
    max_capacity = db.Column(db.Integer)
    fee = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.String(20), default="upcoming")
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    cert_type = db.relationship(
        "CertType",
        back_populates="exams",
    )
    registrations = db.relationship(
        "Registration",
        back_populates="exam",
        lazy="dynamic",
    )
    certificate_records = db.relationship(
        "CertificateRecord",
        back_populates="exam",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Exam {self.exam_name}>"
