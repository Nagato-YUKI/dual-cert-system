"""Certificate record model (证书获取记录表)."""

from app import db


class CertificateRecord(db.Model):
    """Student certificate acquisition record model."""

    __tablename__ = "certificate_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    cert_type_id = db.Column(db.Integer, db.ForeignKey("cert_types.id"))
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"))
    certificate_no = db.Column(db.String(100))
    score = db.Column(db.Numeric(5, 2))
    obtain_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="obtained")
    source = db.Column(db.String(20), default="system")
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    student = db.relationship(
        "Student",
        back_populates="certificate_records",
    )
    cert_type = db.relationship(
        "CertType",
        back_populates="certificate_records",
    )
    exam = db.relationship(
        "Exam",
        back_populates="certificate_records",
    )

    def __repr__(self) -> str:
        return (
            f"<CertificateRecord student={self.student_id} "
            f"cert={self.cert_type_id}>"
        )
