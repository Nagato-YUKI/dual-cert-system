"""Registration model (报名记录表)."""

from app import db


class Registration(db.Model):
    """Student exam registration record model."""

    __tablename__ = "registrations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"))
    status = db.Column(db.String(30), default="pending")
    submit_time = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )
    review_status = db.Column(db.String(20), default="pending")
    ai_review_result = db.Column(db.Text)
    ai_review_score = db.Column(db.Numeric(5, 2))
    human_review_comment = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    reviewed_at = db.Column(db.DateTime)
    materials_path = db.Column(db.String(500))

    # Relationships
    student = db.relationship(
        "Student",
        back_populates="registrations",
    )
    exam = db.relationship(
        "Exam",
        back_populates="registrations",
    )
    reviewer = db.relationship(
        "User",
        back_populates="registrations_reviewed",
    )
    review_logs = db.relationship(
        "ReviewLog",
        back_populates="registration",
        lazy="dynamic",
    )

    __table_args__ = (
        db.UniqueConstraint("student_id", "exam_id", name="uix_student_exam"),
    )

    def __repr__(self) -> str:
        return f"<Registration student={self.student_id} exam={self.exam_id}>"
