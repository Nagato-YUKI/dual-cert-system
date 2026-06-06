"""Models package — unified imports for all database models."""

from app.models.certificate_record import CertificateRecord
from app.models.cert_type import CertType
from app.models.class_ import ClassModel
from app.models.exam import Exam
from app.models.operation_log import OperationLog
from app.models.registration import Registration
from app.models.registration_rule import RegistrationRule
from app.models.review_log import ReviewLog
from app.models.student import Student
from app.models.training_material import TrainingMaterial
from app.models.user import User

__all__ = [
    "CertificateRecord",
    "CertType",
    "ClassModel",
    "Exam",
    "OperationLog",
    "Registration",
    "RegistrationRule",
    "ReviewLog",
    "Student",
    "TrainingMaterial",
    "User",
]
