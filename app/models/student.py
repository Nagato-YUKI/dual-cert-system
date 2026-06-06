"""Student model."""

from app import db


class Student(db.Model):
    """Student information model."""

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    id_card = db.Column(db.String(18))
    avatar_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    class_ = db.relationship(
        "ClassModel",
        back_populates="students",
    )
    registrations = db.relationship(
        "Registration",
        back_populates="student",
        lazy="dynamic",
    )
    certificate_records = db.relationship(
        "CertificateRecord",
        back_populates="student",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Student {self.student_no} {self.name}>"
