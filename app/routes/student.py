"""Student routes module."""

from typing import Optional

from flask import Blueprint, jsonify, request

from app import db
from app.models.cert_type import CertType
from app.models.certificate_record import CertificateRecord
from app.models.exam import Exam
from app.models.registration import Registration
from app.models.student import Student
from app.models.training_material import TrainingMaterial
from app.routes.auth import student_required
from app.services.sms_service import notify_registration_status

student_bp = Blueprint("student", __name__)


# ---------------------------------------------------------------------------
# Certificate Types (public browse)
# ---------------------------------------------------------------------------

@student_bp.route("/cert-types", methods=["GET"])
def list_cert_types():
    """List active certificate types with recommendation flag."""
    category = request.args.get("category")
    query = db.select(CertType).filter_by(status="active")
    if category:
        query = query.filter_by(category=category)
    items = db.session.execute(query).scalars().all()

    # Get current student for recommendation
    from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
    student = None
    try:
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        student = db.session.execute(
            db.select(Student).filter_by(id=user_id)
        ).scalar_one_or_none()
    except Exception:
        pass

    result = []
    for item in items:
        cert_dict = _cert_type_to_dict(item)
        cert_dict["is_recommended_for_me"] = _is_recommended(item, student)
        result.append(cert_dict)
    return jsonify(result)


@student_bp.route("/cert-types/<int:cert_id>", methods=["GET"])
def get_cert_type(cert_id: int):
    """Get certificate type detail with rules."""
    cert = db.session.execute(
        db.select(CertType).filter_by(id=cert_id, status="active")
    ).scalar_one_or_none()
    if not cert:
        return jsonify({"msg": "Certificate type not found"}), 404

    result = _cert_type_to_dict(cert)
    if cert.registration_rule:
        result["rule"] = {
            "rule_content": cert.registration_rule.rule_content,
            "required_grades": cert.registration_rule.required_grades,
            "required_majors": cert.registration_rule.required_majors,
            "prerequisites": cert.registration_rule.prerequisites,
        }
    return jsonify(result)


# ---------------------------------------------------------------------------
# Exams
# ---------------------------------------------------------------------------

@student_bp.route("/exams/data", methods=["GET"])
def list_exams():
    """List upcoming/ongoing exams with registration status for current student."""
    cert_type_id = request.args.get("cert_type_id", type=int)
    query = db.select(Exam).filter(Exam.status.in_(["upcoming", "ongoing"]))
    if cert_type_id:
        query = query.filter_by(cert_type_id=cert_type_id)
    items = db.session.execute(query).scalars().all()

    # Get current student's registered exam ids
    registered_exam_ids = set()
    try:
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        my_registrations = db.session.execute(
            db.select(Registration.exam_id).filter_by(student_id=user_id)
        ).scalars().all()
        registered_exam_ids = set(my_registrations)
    except Exception:
        pass

    return jsonify([
        {**_exam_to_dict(i), "registered": i.id in registered_exam_ids}
        for i in items
    ])


@student_bp.route("/exams/<int:exam_id>/register", methods=["POST"])
@student_required
def register_exam(exam_id: int):
    """Register for an exam."""
    identity = __get_student_identity()
    student_id = identity["id"]

    exam = db.session.execute(
        db.select(Exam).filter_by(id=exam_id)
    ).scalar_one_or_none()
    if not exam:
        return jsonify({"msg": "Exam not found"}), 404

    # Check if already registered
    existing = db.session.execute(
        db.select(Registration).filter_by(student_id=student_id, exam_id=exam_id)
    ).scalar_one_or_none()
    if existing:
        return jsonify({"msg": "Already registered for this exam"}), 409

    # Check capacity
    if exam.max_capacity:
        count = db.session.execute(
            db.select(db.func.count(Registration.id)).filter_by(exam_id=exam_id)
        ).scalar()
        if count >= exam.max_capacity:
            return jsonify({"msg": "Exam is full"}), 409

    reg = Registration(
        student_id=student_id,
        exam_id=exam_id,
        status="pending",
        review_status="pending",
    )
    db.session.add(reg)
    db.session.commit()

    # Send SMS notification if student has phone
    student = db.session.execute(
        db.select(Student).filter_by(id=student_id)
    ).scalar_one_or_none()
    if student and student.phone:
        notify_registration_status(
            phone=student.phone,
            exam_name=exam.exam_name,
            status="报名成功，待审核",
        )

    return jsonify(_registration_to_dict(reg)), 201


# ---------------------------------------------------------------------------
# My Registrations
# ---------------------------------------------------------------------------

@student_bp.route("/my-registrations", methods=["GET"])
@student_required
def my_registrations():
    """Get current student's registration records."""
    identity = __get_student_identity()
    student_id = identity["id"]

    items = db.session.execute(
        db.select(Registration).filter_by(student_id=student_id)
    ).scalars().all()
    return jsonify([_registration_to_dict(i) for i in items])


# ---------------------------------------------------------------------------
# My Certificates
# ---------------------------------------------------------------------------

@student_bp.route("/my-certificates", methods=["GET"])
@student_required
def my_certificates():
    """Get current student's certificate records."""
    identity = __get_student_identity()
    student_id = identity["id"]

    items = db.session.execute(
        db.select(CertificateRecord).filter_by(student_id=student_id)
    ).scalars().all()
    return jsonify([_cert_record_to_dict(i) for i in items])


# ---------------------------------------------------------------------------
# Training Materials (public)
# ---------------------------------------------------------------------------

@student_bp.route("/materials", methods=["GET"])
def list_materials():
    """List public training materials."""
    cert_type_id = request.args.get("cert_type_id", type=int)
    query = db.select(TrainingMaterial).filter_by(is_public=True)
    if cert_type_id:
        query = query.filter_by(cert_type_id=cert_type_id)
    items = db.session.execute(query).scalars().all()
    return jsonify([_material_to_dict(i) for i in items])


@student_bp.route("/materials/<int:material_id>", methods=["GET"])
def get_material(material_id: int):
    """Get public training material detail."""
    material = db.session.execute(
        db.select(TrainingMaterial).filter_by(id=material_id, is_public=True)
    ).scalar_one_or_none()
    if not material:
        return jsonify({"msg": "Material not found"}), 404
    return jsonify(_material_to_dict(material))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def __get_student_identity() -> dict:
    """Get student identity from JWT (called inside student_required)."""
    from flask_jwt_extended import get_jwt_identity

    user_id = int(get_jwt_identity())
    student = db.session.execute(
        db.select(Student).filter_by(id=user_id)
    ).scalar_one_or_none()
    if student:
        return {"id": student.id, "role": "student"}
    return {"id": user_id, "role": "unknown"}


def _cert_type_to_dict(cert: CertType) -> dict:
    return {
        "id": cert.id,
        "name": cert.name,
        "category": cert.category,
        "description": cert.description,
        "issuing_authority": cert.issuing_authority,
        "is_required": cert.is_required,
        "is_recommended": cert.is_recommended,
        "status": cert.status,
        "created_at": cert.created_at.isoformat() if cert.created_at else None,
    }


def _exam_to_dict(exam: Exam) -> dict:
    return {
        "id": exam.id,
        "cert_type_id": exam.cert_type_id,
        "exam_name": exam.exam_name,
        "exam_date": exam.exam_date.isoformat() if exam.exam_date else None,
        "registration_start": exam.registration_start.isoformat()
        if exam.registration_start
        else None,
        "registration_end": exam.registration_end.isoformat()
        if exam.registration_end
        else None,
        "exam_location": exam.exam_location,
        "max_capacity": exam.max_capacity,
        "fee": float(exam.fee) if exam.fee else 0,
        "status": exam.status,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
    }


def _registration_to_dict(reg: Registration) -> dict:
    return {
        "id": reg.id,
        "student_id": reg.student_id,
        "exam_id": reg.exam_id,
        "exam_name": reg.exam.exam_name if reg.exam else None,
        "status": reg.status,
        "submit_time": reg.submit_time.isoformat() if reg.submit_time else None,
        "review_status": reg.review_status,
        "ai_review_score": float(reg.ai_review_score) if reg.ai_review_score else None,
        "human_review_comment": reg.human_review_comment,
        "reviewed_at": reg.reviewed_at.isoformat() if reg.reviewed_at else None,
    }


def _cert_record_to_dict(record: CertificateRecord) -> dict:
    return {
        "id": record.id,
        "student_id": record.student_id,
        "cert_type_id": record.cert_type_id,
        "cert_type_name": record.cert_type.name if record.cert_type else None,
        "exam_id": record.exam_id,
        "certificate_no": record.certificate_no,
        "score": float(record.score) if record.score else None,
        "obtain_date": record.obtain_date.isoformat() if record.obtain_date else None,
        "status": record.status,
        "source": record.source,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def _material_to_dict(material: TrainingMaterial) -> dict:
    return {
        "id": material.id,
        "cert_type_id": material.cert_type_id,
        "title": material.title,
        "content": material.content,
        "file_path": material.file_path,
        "material_type": material.material_type,
        "is_public": material.is_public,
        "created_at": material.created_at.isoformat() if material.created_at else None,
    }


def _is_recommended(cert_type: CertType, student: Optional[Student]) -> bool:
    """Check if a certificate type is recommended for the given student.

    Rules:
    1. If cert_type.is_recommended is True, it's globally recommended.
    2. If registration_rule exists, match student's grade/major.
    3. If student has no class info, return global recommendation only.
    """
    if not student:
        return bool(cert_type.is_recommended)

    # Global recommendation
    if cert_type.is_recommended:
        return True

    # Rule-based recommendation
    rule = cert_type.registration_rule
    if not rule:
        return False

    student_grade = student.class_.grade if student.class_ else None
    student_major = student.class_.major if student.class_ else None

    # Check grade match
    if rule.required_grades and student_grade:
        grades = [g.strip() for g in rule.required_grades.split(",")]
        if student_grade in grades:
            return True

    # Check major match
    if rule.required_majors and student_major:
        majors = [m.strip() for m in rule.required_majors.split(",")]
        if student_major in majors:
            return True

    return False
