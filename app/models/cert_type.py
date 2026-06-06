"""Certificate type model."""

from app import db


class CertType(db.Model):
    """Certificate type model."""

    __tablename__ = "cert_types"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(
        db.String(50),
        nullable=False,
        comment="分类：人社证书/专业证书/校内引进",
    )
    description = db.Column(db.Text)
    issuing_authority = db.Column(db.String(200))
    is_required = db.Column(db.Boolean, default=False)
    is_recommended = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    exams = db.relationship(
        "Exam",
        back_populates="cert_type",
        lazy="dynamic",
    )
    training_materials = db.relationship(
        "TrainingMaterial",
        back_populates="cert_type",
        lazy="dynamic",
    )
    registration_rule = db.relationship(
        "RegistrationRule",
        back_populates="cert_type",
        uselist=False,
    )
    certificate_records = db.relationship(
        "CertificateRecord",
        back_populates="cert_type",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<CertType {self.name} ({self.category})>"
