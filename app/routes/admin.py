"""Admin routes module."""

import os

from flask import Blueprint, jsonify, request, send_file

from app import db
from app.models.cert_type import CertType
from app.models.certificate_record import CertificateRecord
from app.models.exam import Exam
from app.models.registration import Registration
from app.models.registration_rule import RegistrationRule
from app.models.student import Student
from app.models.training_material import TrainingMaterial
from app.routes.auth import admin_required
from app.services.archive_service import (
    archive_by_exam,
    export_archive,
    list_archive_by_class,
)
from app.services.audit_service import log_operation
from app.services.import_service import (
    generate_template,
    import_cert_records,
    import_exam_results,
    import_students,
)
from app.services.ai_review import ai_review_registration
from app.services.sms_service import notify_registration_status
from app.models.review_log import ReviewLog

admin_bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------------------
# Certificate Type CRUD
# ---------------------------------------------------------------------------

@admin_bp.route("/cert-types", methods=["GET"])
@admin_required
def list_cert_types():
    """List all certificate types."""
    category = request.args.get("category")
    query = db.select(CertType)
    if category:
        query = query.filter_by(category=category)
    items = db.session.execute(query).scalars().all()
    return jsonify([_cert_type_to_dict(i) for i in items])


@admin_bp.route("/cert-types", methods=["POST"])
@admin_required
@log_operation(action="create_cert_type", target_type="cert_type")
def create_cert_type():
    """Create a new certificate type."""
    data = request.get_json(silent=True) or {}
    required = ["name", "category"]
    for field in required:
        if not data.get(field):
            return jsonify({"msg": f"Field '{field}' is required"}), 400

    cert = CertType(
        name=data["name"],
        category=data["category"],
        description=data.get("description"),
        issuing_authority=data.get("issuing_authority"),
        is_required=data.get("is_required", False),
        is_recommended=data.get("is_recommended", False),
        status=data.get("status", "active"),
    )
    db.session.add(cert)
    db.session.commit()
    return jsonify(_cert_type_to_dict(cert)), 201


@admin_bp.route("/cert-types/<int:cert_id>", methods=["PUT"])
@admin_required
@log_operation(action="update_cert_type", target_type="cert_type", get_target_id=lambda cert_id, **kw: cert_id)
def update_cert_type(cert_id: int):
    """Update a certificate type."""
    cert = db.session.execute(
        db.select(CertType).filter_by(id=cert_id)
    ).scalar_one_or_none()
    if not cert:
        return jsonify({"msg": "Certificate type not found"}), 404

    data = request.get_json(silent=True) or {}
    cert.name = data.get("name", cert.name)
    cert.category = data.get("category", cert.category)
    cert.description = data.get("description", cert.description)
    cert.issuing_authority = data.get("issuing_authority", cert.issuing_authority)
    cert.is_required = data.get("is_required", cert.is_required)
    cert.is_recommended = data.get("is_recommended", cert.is_recommended)
    cert.status = data.get("status", cert.status)
    db.session.commit()
    return jsonify(_cert_type_to_dict(cert))


@admin_bp.route("/cert-types/<int:cert_id>", methods=["DELETE"])
@admin_required
@log_operation(action="delete_cert_type", target_type="cert_type", get_target_id=lambda cert_id, **kw: cert_id)
def delete_cert_type(cert_id: int):
    """Delete a certificate type."""
    cert = db.session.execute(
        db.select(CertType).filter_by(id=cert_id)
    ).scalar_one_or_none()
    if not cert:
        return jsonify({"msg": "Certificate type not found"}), 404

    db.session.delete(cert)
    db.session.commit()
    return jsonify({"msg": "Deleted successfully"})


@admin_bp.route("/cert-types/<int:cert_id>/rules", methods=["GET"])
@admin_required
def get_cert_rules(cert_id: int):
    """Get registration rules for a certificate type."""
    rule = db.session.execute(
        db.select(RegistrationRule).filter_by(cert_type_id=cert_id)
    ).scalar_one_or_none()
    if not rule:
        return jsonify({"msg": "Rule not found"}), 404
    return jsonify(_rule_to_dict(rule))


@admin_bp.route("/cert-types/<int:cert_id>/rules", methods=["PUT"])
@admin_required
def update_cert_rules(cert_id: int):
    """Create or update registration rules for a certificate type."""
    cert = db.session.execute(
        db.select(CertType).filter_by(id=cert_id)
    ).scalar_one_or_none()
    if not cert:
        return jsonify({"msg": "Certificate type not found"}), 404

    data = request.get_json(silent=True) or {}
    rule = db.session.execute(
        db.select(RegistrationRule).filter_by(cert_type_id=cert_id)
    ).scalar_one_or_none()

    if rule:
        rule.rule_content = data.get("rule_content", rule.rule_content)
        rule.required_grades = data.get("required_grades", rule.required_grades)
        rule.required_majors = data.get("required_majors", rule.required_majors)
        rule.prerequisites = data.get("prerequisites", rule.prerequisites)
    else:
        rule = RegistrationRule(
            cert_type_id=cert_id,
            rule_content=data.get("rule_content", ""),
            required_grades=data.get("required_grades"),
            required_majors=data.get("required_majors"),
            prerequisites=data.get("prerequisites"),
        )
        db.session.add(rule)

    db.session.commit()
    return jsonify(_rule_to_dict(rule))


# ---------------------------------------------------------------------------
# Exam CRUD
# ---------------------------------------------------------------------------

@admin_bp.route("/exams", methods=["GET"])
@admin_required
def list_exams():
    """List exams with optional filters."""
    cert_type_id = request.args.get("cert_type_id", type=int)
    status = request.args.get("status")
    query = db.select(Exam)
    if cert_type_id:
        query = query.filter_by(cert_type_id=cert_type_id)
    if status:
        query = query.filter_by(status=status)
    items = db.session.execute(query).scalars().all()
    return jsonify([_exam_to_dict(i) for i in items])


@admin_bp.route("/exams", methods=["POST"])
@admin_required
@log_operation(action="create_exam", target_type="exam", get_details=lambda **kw: f"Created exam: {kw.get('result', [{}])[0].get('exam_name', '')}")
def create_exam():
    """Create a new exam."""
    data = request.get_json(silent=True) or {}
    if not data.get("exam_name"):
        return jsonify({"msg": "Field 'exam_name' is required"}), 400

    exam = Exam(
        cert_type_id=data.get("cert_type_id"),
        exam_name=data["exam_name"],
        exam_date=data.get("exam_date"),
        registration_start=data.get("registration_start"),
        registration_end=data.get("registration_end"),
        exam_location=data.get("exam_location"),
        max_capacity=data.get("max_capacity"),
        fee=data.get("fee", 0),
        status=data.get("status", "upcoming"),
    )
    db.session.add(exam)
    db.session.commit()
    return jsonify(_exam_to_dict(exam)), 201


@admin_bp.route("/exams/<int:exam_id>", methods=["PUT"])
@admin_required
@log_operation(action="update_exam", target_type="exam", get_target_id=lambda exam_id, **kw: exam_id)
def update_exam(exam_id: int):
    """Update an exam."""
    exam = db.session.execute(
        db.select(Exam).filter_by(id=exam_id)
    ).scalar_one_or_none()
    if not exam:
        return jsonify({"msg": "Exam not found"}), 404

    data = request.get_json(silent=True) or {}
    exam.cert_type_id = data.get("cert_type_id", exam.cert_type_id)
    exam.exam_name = data.get("exam_name", exam.exam_name)
    exam.exam_date = data.get("exam_date", exam.exam_date)
    exam.registration_start = data.get("registration_start", exam.registration_start)
    exam.registration_end = data.get("registration_end", exam.registration_end)
    exam.exam_location = data.get("exam_location", exam.exam_location)
    exam.max_capacity = data.get("max_capacity", exam.max_capacity)
    exam.fee = data.get("fee", exam.fee)
    exam.status = data.get("status", exam.status)
    db.session.commit()
    return jsonify(_exam_to_dict(exam))


@admin_bp.route("/exams/<int:exam_id>", methods=["DELETE"])
@admin_required
@log_operation(action="delete_exam", target_type="exam", get_target_id=lambda exam_id, **kw: exam_id)
def delete_exam(exam_id: int):
    """Delete an exam."""
    exam = db.session.execute(
        db.select(Exam).filter_by(id=exam_id)
    ).scalar_one_or_none()
    if not exam:
        return jsonify({"msg": "Exam not found"}), 404

    db.session.delete(exam)
    db.session.commit()
    return jsonify({"msg": "Deleted successfully"})


# ---------------------------------------------------------------------------
# Reviews (merged from review.py to avoid blueprint conflict)
# ---------------------------------------------------------------------------

@admin_bp.route("/reviews", methods=["GET"])
@admin_required
def list_reviews():
    """List registrations pending or under review."""
    status = request.args.get("status", "")
    review_status = request.args.get("review_status")

    query = db.select(Registration)
    if status:
        query = query.filter_by(status=status)
    if review_status:
        query = query.filter_by(review_status=review_status)

    items = db.session.execute(query).scalars().all()
    return jsonify([_registration_to_dict(i) for i in items])


@admin_bp.route("/reviews/<int:reg_id>/ai", methods=["POST"])
@admin_required
@log_operation(action="ai_review", target_type="registration", get_target_id=lambda reg_id, **kw: reg_id)
def trigger_ai_review(reg_id: int):
    """Trigger AI review for a single registration."""
    reg = db.session.execute(
        db.select(Registration).filter_by(id=reg_id)
    ).scalar_one_or_none()
    if not reg:
        return jsonify({"msg": "Registration not found"}), 404

    import json
    result = ai_review_registration(reg)

    reg.ai_review_result = json.dumps(result, ensure_ascii=False)
    reg.ai_review_score = result["score"]

    if result["score"] >= 80 and result["result"] == "approved":
        reg.review_status = "ai_reviewed"
        reg.status = "approved"
    else:
        reg.review_status = "ai_reviewed"

    log = ReviewLog(
        registration_id=reg.id,
        review_type="ai_review",
        result=result["result"],
        comment=result["reason"],
        score=result["score"],
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"msg": "AI review completed", "result": result})


@admin_bp.route("/reviews/batch-ai", methods=["POST"])
@admin_required
@log_operation(action="batch_ai_review", target_type="registration")
def batch_ai_review():
    """Trigger AI review for multiple registrations."""
    data = request.get_json(silent=True) or {}
    reg_ids = data.get("ids", [])
    if not reg_ids:
        return jsonify({"msg": "No registration IDs provided"}), 400

    import json
    results = []
    for reg_id in reg_ids:
        reg = db.session.execute(
            db.select(Registration).filter_by(id=reg_id)
        ).scalar_one_or_none()
        if not reg:
            results.append({"id": reg_id, "msg": "Not found"})
            continue

        result = ai_review_registration(reg)
        reg.ai_review_result = json.dumps(result, ensure_ascii=False)
        reg.ai_review_score = result["score"]

        if result["score"] >= 80 and result["result"] == "approved":
            reg.review_status = "ai_reviewed"
            reg.status = "approved"
        else:
            reg.review_status = "ai_reviewed"

        log = ReviewLog(
            registration_id=reg.id,
            review_type="ai_review",
            result=result["result"],
            comment=result["reason"],
            score=result["score"],
        )
        db.session.add(log)
        results.append({"id": reg_id, "msg": "Reviewed", "result": result})

    db.session.commit()
    return jsonify({"results": results})


@admin_bp.route("/reviews/<int:reg_id>", methods=["PUT"])
@admin_required
@log_operation(action="human_review", target_type="registration", get_target_id=lambda reg_id, **kw: reg_id)
def human_review(reg_id: int):
    """Human review a registration."""
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    comment = data.get("comment", "")

    if action not in ("approved", "rejected", "need_more_info"):
        return jsonify({"msg": "Invalid action"}), 400

    reg = db.session.execute(
        db.select(Registration).filter_by(id=reg_id)
    ).scalar_one_or_none()
    if not reg:
        return jsonify({"msg": "Registration not found"}), 404

    reviewer_id = int(get_jwt_identity())

    if action == "approved":
        reg.status = "approved"
        reg.review_status = "approved"
    elif action == "rejected":
        reg.status = "rejected"
        reg.review_status = "rejected"
    else:
        reg.review_status = "need_more_info"

    reg.human_review_comment = comment
    reg.reviewed_by = reviewer_id
    reg.reviewed_at = db.func.current_timestamp()

    log = ReviewLog(
        registration_id=reg.id,
        reviewer_id=reviewer_id,
        review_type="human_review",
        result=action,
        comment=comment,
    )
    db.session.add(log)
    db.session.commit()

    student_phone = reg.student.phone if reg.student else None
    if student_phone:
        notify_registration_status(
            phone=student_phone,
            exam_name=reg.exam.exam_name if reg.exam else "未知考试",
            status="已通过" if action == "approved" else "未通过" if action == "rejected" else "需补充材料",
            review_comment=comment,
        )

    return jsonify({"msg": f"Registration {action}"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _registration_to_dict(reg: Registration) -> dict:
    return {
        "id": reg.id,
        "student_id": reg.student_id,
        "student_name": reg.student.name if reg.student else None,
        "student_no": reg.student.student_no if reg.student else None,
        "class_name": reg.student.class_.name if reg.student and reg.student.class_ else None,
        "exam_id": reg.exam_id,
        "exam_name": reg.exam.exam_name if reg.exam else None,
        "status": reg.status,
        "submit_time": reg.submit_time.isoformat() if reg.submit_time else None,
        "review_status": reg.review_status,
        "ai_review_score": float(reg.ai_review_score) if reg.ai_review_score else None,
        "ai_review_result": reg.ai_review_result,
        "human_review_comment": reg.human_review_comment,
        "reviewed_at": reg.reviewed_at.isoformat() if reg.reviewed_at else None,
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


def _rule_to_dict(rule: RegistrationRule) -> dict:
    return {
        "id": rule.id,
        "cert_type_id": rule.cert_type_id,
        "rule_content": rule.rule_content,
        "required_grades": rule.required_grades,
        "required_majors": rule.required_majors,
        "prerequisites": rule.prerequisites,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Batch Import
# ---------------------------------------------------------------------------

@admin_bp.route("/import/<import_type>", methods=["POST"])
@admin_required
def import_data(import_type: str):
    """Import data from uploaded file."""
    if "file" not in request.files:
        return jsonify({"msg": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"msg": "Empty filename"}), 400

    upload_folder = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)

    try:
        if import_type == "students":
            result = import_students(file_path)
        elif import_type == "exam_results":
            result = import_exam_results(file_path)
        elif import_type == "cert_records":
            result = import_cert_records(file_path)
        else:
            return jsonify({"msg": "Unknown import type"}), 400
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

    return jsonify(result)


@admin_bp.route("/import/template/<import_type>", methods=["GET"])
@admin_required
def download_template(import_type: str):
    """Download import template."""
    try:
        path = generate_template(import_type)
        return send_file(path, as_attachment=True)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400


# ---------------------------------------------------------------------------
# Training Materials (admin CRUD)
# ---------------------------------------------------------------------------

@admin_bp.route("/materials", methods=["GET"])
@admin_required
def list_materials_admin():
    """List all training materials (admin)."""
    cert_type_id = request.args.get("cert_type_id", type=int)
    query = db.select(TrainingMaterial)
    if cert_type_id:
        query = query.filter_by(cert_type_id=cert_type_id)
    items = db.session.execute(query).scalars().all()
    return jsonify([_material_to_dict(i) for i in items])


@admin_bp.route("/materials", methods=["POST"])
@admin_required
def create_material():
    """Create a training material."""
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return jsonify({"msg": "Title is required"}), 400

    material = TrainingMaterial(
        cert_type_id=data.get("cert_type_id"),
        title=data["title"],
        content=data.get("content"),
        file_path=data.get("file_path"),
        material_type=data.get("material_type", "document"),
        is_public=data.get("is_public", True),
    )
    db.session.add(material)
    db.session.commit()
    return jsonify(_material_to_dict(material)), 201


@admin_bp.route("/materials/<int:material_id>", methods=["PUT"])
@admin_required
def update_material(material_id: int):
    """Update a training material."""
    material = db.session.execute(
        db.select(TrainingMaterial).filter_by(id=material_id)
    ).scalar_one_or_none()
    if not material:
        return jsonify({"msg": "Material not found"}), 404

    data = request.get_json(silent=True) or {}
    material.cert_type_id = data.get("cert_type_id", material.cert_type_id)
    material.title = data.get("title", material.title)
    material.content = data.get("content", material.content)
    material.file_path = data.get("file_path", material.file_path)
    material.material_type = data.get("material_type", material.material_type)
    material.is_public = data.get("is_public", material.is_public)
    db.session.commit()
    return jsonify(_material_to_dict(material))


@admin_bp.route("/materials/<int:material_id>", methods=["DELETE"])
@admin_required
def delete_material(material_id: int):
    """Delete a training material."""
    material = db.session.execute(
        db.select(TrainingMaterial).filter_by(id=material_id)
    ).scalar_one_or_none()
    if not material:
        return jsonify({"msg": "Material not found"}), 404

    db.session.delete(material)
    db.session.commit()
    return jsonify({"msg": "Deleted successfully"})


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


# ---------------------------------------------------------------------------
# Archive Management
# ---------------------------------------------------------------------------

@admin_bp.route("/archive/exam/<int:exam_id>", methods=["POST"])
@admin_required
def trigger_archive(exam_id: int):
    """Trigger archive for an exam."""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "archive")
    result = archive_by_exam(exam_id, base_dir)
    return jsonify(result)


@admin_bp.route("/archive/classes", methods=["GET"])
@admin_required
def list_archives():
    """List archives grouped by class."""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "archive")
    result = list_archive_by_class(base_dir)
    return jsonify(result)


@admin_bp.route("/archive/export/<int:exam_id>", methods=["GET"])
@admin_required
def export_archive_file(exam_id: int):
    """Export archive as zip."""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "archive")
    export_dir = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "exports")
    try:
        zip_path = export_archive(exam_id, base_dir, export_dir)
        return send_file(zip_path, as_attachment=True)
    except ValueError as e:
        return jsonify({"msg": str(e)}), 400


# ---------------------------------------------------------------------------
# Operation Logs
# ---------------------------------------------------------------------------

@admin_bp.route("/logs", methods=["GET"])
@admin_required
def list_operation_logs():
    """List operation logs with optional filters."""
    from app.models.operation_log import OperationLog

    action = request.args.get("action")
    target_type = request.args.get("target_type")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = db.select(OperationLog).order_by(OperationLog.created_at.desc())
    if action:
        query = query.filter_by(action=action)
    if target_type:
        query = query.filter_by(target_type=target_type)

    pagination = db.paginate(query, page=page, per_page=per_page)
    return jsonify({
        "items": [_log_to_dict(i) for i in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
        "per_page": per_page,
    })


def _log_to_dict(log) -> dict:
    return {
        "id": log.id,
        "user_id": log.user_id,
        "user_name": log.user.username if log.user else None,
        "student_id": log.student_id,
        "student_name": log.student.name if log.student else None,
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "details": log.details,
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


# ---------------------------------------------------------------------------
# Big Screen Data
# ---------------------------------------------------------------------------

@admin_bp.route("/bigscreen/data", methods=["GET"])
@admin_required
def bigscreen_data():
    """Aggregate data for big screen visualization."""
    # Total counts
    total_certs = db.session.execute(
        db.select(db.func.count(CertType.id))
    ).scalar()
    total_exams = db.session.execute(
        db.select(db.func.count(Exam.id))
    ).scalar()
    total_students = db.session.execute(
        db.select(db.func.count(Student.id))
    ).scalar()
    total_registrations = db.session.execute(
        db.select(db.func.count(Registration.id))
    ).scalar()

    # Registration status distribution
    reg_status_counts = db.session.execute(
        db.select(Registration.status, db.func.count(Registration.id))
        .group_by(Registration.status)
    ).all()

    # Certificate category distribution
    cert_category_counts = db.session.execute(
        db.select(CertType.category, db.func.count(CertType.id))
        .group_by(CertType.category)
    ).all()

    # Monthly registration trend (last 6 months)
    from sqlalchemy import func
    from datetime import datetime, timedelta
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_trend = db.session.execute(
        db.select(
            func.to_char(Registration.submit_time, 'YYYY-MM').label('month'),
            func.count(Registration.id)
        )
        .where(Registration.submit_time >= six_months_ago)
        .group_by('month')
        .order_by('month')
    ).all()

    # Top 5 exams by registration count
    top_exams = db.session.execute(
        db.select(Exam.exam_name, db.func.count(Registration.id))
        .join(Registration, Exam.id == Registration.exam_id)
        .group_by(Exam.id)
        .order_by(db.func.count(Registration.id).desc())
        .limit(5)
    ).all()

    # Class distribution
    from app.models.class_ import ClassModel
    class_distribution = db.session.execute(
        db.select(Student.class_id, db.func.count(Student.id))
        .group_by(Student.class_id)
    ).all()
    class_names = []
    class_counts = []
    for cid, count in class_distribution:
        class_obj = db.session.execute(
            db.select(ClassModel).filter_by(id=cid)
        ).scalar_one_or_none() if cid else None
        class_names.append(class_obj.name if class_obj else "未分类")
        class_counts.append(count)

    return jsonify({
        "total_certs": total_certs,
        "total_exams": total_exams,
        "total_students": total_students,
        "total_registrations": total_registrations,
        "reg_status_distribution": [
            {"status": s, "count": c} for s, c in reg_status_counts
        ],
        "cert_category_distribution": [
            {"category": c, "count": n} for c, n in cert_category_counts
        ],
        "monthly_trend": [
            {"month": str(m), "count": c} for m, c in monthly_trend
        ],
        "top_exams": [
            {"exam_name": n, "count": c} for n, c in top_exams
        ],
        "class_distribution": {
            "names": class_names,
            "counts": class_counts,
        },
    })
