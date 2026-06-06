"""Class model (班级表)."""

from app import db


class ClassModel(db.Model):
    """Class/Classroom model representing a student class."""

    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(20))
    major = db.Column(db.String(100))
    department = db.Column(db.String(100))
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    students = db.relationship(
        "Student",
        back_populates="class_",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<ClassModel {self.name}>"
