"""External API routes module for edu system integration.

Provides RESTful endpoints for external systems to query student info
and certificate records. Protected by API Key authentication.
"""

import os
from functools import wraps

from flask import Blueprint, jsonify, request

from app import db
from app.models.certificate_record import CertificateRecord
from app.models.student import Student

api_bp = Blueprint("api", __name__)

# In-memory API key store (can be moved to database in production)
API_KEYS = set()
_DEFAULT_API_KEY = os.environ.get("EDU_API_KEY")
if _DEFAULT_API_KEY:
    API_KEYS.add(_DEFAULT_API_KEY)


def require_api_key(fn):
    """Decorator to require a valid API key in the X-API-Key header."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key", "")
        if not key or key not in API_KEYS:
            return jsonify({"msg": "Invalid or missing API key"}), 401
        return fn(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "dual-cert-system"})


# ---------------------------------------------------------------------------
# Student Query
# ---------------------------------------------------------------------------

@api_bp.route("/students", methods=["GET"])
@require_api_key
def list_students():
    """List students with optional filters."""
    class_name = request.args.get("class_name")
    student_no = request.args.get("student_no")

    query = db.select(Student)
    if class_name:
        query = query.join(Student.class_).filter_by(name=class_name)
    if student_no:
        query = query.filter_by(student_no=student_no)

    items = db.session.execute(query).scalars().all()
    return jsonify([_student_to_dict(i) for i in items])


@api_bp.route("/students/<int:student_id>", methods=["GET"])
@require_api_key
def get_student(student_id: int):
    """Get a single student by ID."""
    student = db.session.execute(
        db.select(Student).filter_by(id=student_id)
    ).scalar_one_or_none()
    if not student:
        return jsonify({"msg": "Student not found"}), 404
    return jsonify(_student_to_dict(student))


# ---------------------------------------------------------------------------
# Certificate Records Sync
# ---------------------------------------------------------------------------

@api_bp.route("/cert-records", methods=["GET"])
@require_api_key
def list_cert_records():
    """List certificate records with optional filters."""
    student_no = request.args.get("student_no")
    cert_type_id = request.args.get("cert_type_id", type=int)

    query = db.select(CertificateRecord)
    if student_no:
        query = query.join(CertificateRecord.student).filter_by(student_no=student_no)
    if cert_type_id:
        query = query.filter_by(cert_type_id=cert_type_id)

    items = db.session.execute(query).scalars().all()
    return jsonify([_cert_record_to_dict(i) for i in items])


@api_bp.route("/cert-records", methods=["POST"])
@require_api_key
def create_cert_record():
    """Create a certificate record (sync from external system)."""
    data = request.get_json(silent=True) or {}
    required = ["student_no", "cert_type_id"]
    for field in required:
        if not data.get(field):
            return jsonify({"msg": f"Field '{field}' is required"}), 400

    student = db.session.execute(
        db.select(Student).filter_by(student_no=data["student_no"])
    ).scalar_one_or_none()
    if not student:
        return jsonify({"msg": "Student not found"}), 404

    record = CertificateRecord(
        student_id=student.id,
        cert_type_id=data["cert_type_id"],
        exam_id=data.get("exam_id"),
        certificate_no=data.get("certificate_no"),
        score=data.get("score"),
        obtain_date=data.get("obtain_date"),
        status=data.get("status", "obtained"),
        source="external_api",
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(_cert_record_to_dict(record)), 201


# ---------------------------------------------------------------------------
# API Key Management (admin only, simple implementation)
# ---------------------------------------------------------------------------

@api_bp.route("/keys", methods=["POST"])
def create_api_key():
    """Generate a new API key (requires admin secret)."""
    admin_secret = request.headers.get("X-Admin-Secret", "")
    expected = os.environ.get("ADMIN_SECRET", "")
    if not expected or admin_secret != expected:
        return jsonify({"msg": "Unauthorized"}), 403

    import secrets

    new_key = secrets.token_urlsafe(32)
    API_KEYS.add(new_key)
    return jsonify({"api_key": new_key})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _student_to_dict(student: Student) -> dict:
    return {
        "id": student.id,
        "student_no": student.student_no,
        "name": student.name,
        "class_name": student.class_.name if student.class_ else None,
        "grade": student.class_.grade if student.class_ else None,
        "major": student.class_.major if student.class_ else None,
        "phone": student.phone,
        "email": student.email,
        "status": student.status,
    }


def _cert_record_to_dict(record: CertificateRecord) -> dict:
    return {
        "id": record.id,
        "student_no": record.student.student_no if record.student else None,
        "student_name": record.student.name if record.student else None,
        "cert_type_id": record.cert_type_id,
        "cert_type_name": record.cert_type.name if record.cert_type else None,
        "certificate_no": record.certificate_no,
        "score": float(record.score) if record.score else None,
        "obtain_date": record.obtain_date.isoformat() if record.obtain_date else None,
        "status": record.status,
        "source": record.source,
    }
