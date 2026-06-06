"""Registration rule model (报名规则表)."""

from app import db


class RegistrationRule(db.Model):
    """Registration rule model tied to a certificate type."""

    __tablename__ = "registration_rules"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cert_type_id = db.Column(
        db.Integer,
        db.ForeignKey("cert_types.id"),
        unique=True,
    )
    rule_content = db.Column(db.Text, nullable=False)
    required_grades = db.Column(db.String(200))
    required_majors = db.Column(db.Text)
    prerequisites = db.Column(db.Text)
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
    )

    # Relationships
    cert_type = db.relationship(
        "CertType",
        back_populates="registration_rule",
    )

    def __repr__(self) -> str:
        return f"<RegistrationRule cert_type={self.cert_type_id}>"
