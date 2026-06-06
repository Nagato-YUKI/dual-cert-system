"""Training material model (培训材料表)."""

from app import db


class TrainingMaterial(db.Model):
    """Training material model for certificate types."""

    __tablename__ = "training_materials"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cert_type_id = db.Column(db.Integer, db.ForeignKey("cert_types.id"))
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    material_type = db.Column(db.String(30), default="document")
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    cert_type = db.relationship(
        "CertType",
        back_populates="training_materials",
    )

    def __repr__(self) -> str:
        return f"<TrainingMaterial {self.title}>"
