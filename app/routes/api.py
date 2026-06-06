"""External API routes module for edu system integration.

Provides RESTful endpoints for external systems to query student info
and certificate records. Protected by API Key authentication.
Also provides AI chatbot endpoint for certificate knowledge base Q&A.
"""

import json
import os
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

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
# AI Chatbot (Knowledge Base Q&A)
# ---------------------------------------------------------------------------

_kb_cache: dict | None = None


def _load_knowledge_base() -> dict:
    """Load and cache the knowledge base JSON file."""
    global _kb_cache
    if _kb_cache is not None:
        return _kb_cache
    kb_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "static",
        "data",
        "knowledge_base.json",
    )
    with open(kb_path, "r", encoding="utf-8") as f:
        _kb_cache = json.load(f)
    return _kb_cache


def _match_certificate(message: str, kb: dict) -> dict | None:
    """Find the best matching certificate based on keywords in the message."""
    msg_lower = message.lower()
    best_match = None
    best_score = 0
    for cert in kb.get("certificates", []):
        score = 0
        for kw in cert.get("keywords", []):
            if kw.lower() in msg_lower:
                score += len(kw)
        if score > best_score:
            best_score = score
            best_match = cert
    return best_match


def _match_general_qa(message: str, kb: dict) -> str | None:
    """Find a matching general Q&A answer based on keywords."""
    msg_lower = message.lower()
    best_match = None
    best_score = 0
    for item in kb.get("general_qa", []):
        score = 0
        for kw in item.get("keywords", []):
            if kw.lower() in msg_lower:
                score += len(kw)
        if score > best_score:
            best_score = score
            best_match = item
    if best_match and best_score > 0:
        return best_match["answer"]
    return None


def _build_cert_reply(cert: dict, message: str) -> str:
    """Build a detailed reply for a matched certificate."""
    msg_lower = message.lower()
    parts: list[str] = []

    # Check what aspect the user is asking about
    asking_conditions = any(
        w in msg_lower
        for w in ["条件", "要求", "资格", "能不能考", "可以考", "报名条件"]
    )
    asking_time = any(
        w in msg_lower for w in ["时间", "什么时候", "几月", "几号", "日程"]
    )
    asking_fee = any(w in msg_lower for w in ["费用", "多少钱", "收费", "价格"])
    asking_subject = any(
        w in msg_lower for w in ["科目", "考什么", "内容", "题型", "形式"]
    )
    asking_score = any(
        w in msg_lower for w in ["及格", "通过", "分数线", "多少分", "过线"]
    )
    asking_validity = any(w in msg_lower for w in ["有效期", "有效", "过期"])
    asking_material = any(
        w in msg_lower for w in ["材料", "准备什么", "需要什么", "带什么"]
    )
    asking_faq = any(w in msg_lower for w in ["问题", "常见", "faq"])

    # If no specific aspect, provide overview
    asking_overview = not any(
        [
            asking_conditions,
            asking_time,
            asking_fee,
            asking_subject,
            asking_score,
            asking_validity,
            asking_material,
            asking_faq,
        ]
    )

    if asking_overview or asking_conditions:
        req = cert.get("requirements", {})
        parts.append(
            f"【{cert['name']} - 报名条件】\n"
            f"学历要求：{req.get('education', '暂无')}\n"
            f"前置证书：{req.get('prerequisite', '暂无')}\n"
            f"其他：{req.get('other', '暂无')}"
        )

    if asking_overview or asking_time:
        sched = cert.get("exam_schedule", {})
        parts.append(
            f"【考试时间】\n"
            f"考试频次：{sched.get('frequency', '暂无')}\n"
            f"考试月份：{'、'.join(sched.get('months', []))}\n"
            f"报名时间：{sched.get('registration_time', '暂无')}"
        )

    if asking_overview or asking_fee:
        fee = cert.get("fees", {})
        parts.append(
            f"【考试费用】\n"
            f"金额：{fee.get('amount', '暂无')}\n"
            f"备注：{fee.get('note', '')}"
        )

    if asking_overview or asking_subject:
        subjects = cert.get("subjects", [])
        subj_lines = []
        for s in subjects:
            subj_lines.append(
                f"  - {s['name']}：{s['format']}，时长{s['duration']}，满分{s['total_score']}分"
            )
        parts.append(f"【考试科目】\n" + "\n".join(subj_lines))

    if asking_overview or asking_score:
        parts.append(f"【通过标准】\n分数线：{cert.get('passing_score', '暂无')}分")

    if asking_overview or asking_validity:
        parts.append(f"【证书有效期】\n{cert.get('validity', '暂无')}")

    if asking_material:
        materials = cert.get("required_materials", [])
        parts.append(
            f"【报名所需材料】\n" + "\n".join(f"  {i+1}. {m}" for i, m in enumerate(materials))
        )

    if asking_faq:
        faq_list = cert.get("faq", [])
        if faq_list:
            faq_lines = [f"  Q: {f['q']}\n  A: {f['a']}" for f in faq_list]
            parts.append("【常见问题】\n" + "\n\n".join(faq_lines))

    return "\n\n".join(parts) if parts else f"暂无{cert['name']}的详细信息。"


@api_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    """AI chatbot endpoint: answer student questions based on knowledge base."""
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"reply": "请输入您的问题，我来帮您解答。"})

    kb = _load_knowledge_base()

    # 1. Try to match a specific certificate
    cert = _match_certificate(message, kb)
    if cert:
        reply = _build_cert_reply(cert, message)
        return jsonify({"reply": reply})

    # 2. Try to match general Q&A
    general_answer = _match_general_qa(message, kb)
    if general_answer:
        return jsonify({"reply": general_answer})

    # 3. Fallback reply
    cert_names = "、".join(c["name"] for c in kb.get("certificates", []))
    return jsonify(
        {
            "reply": (
                f"抱歉，我没有找到与您问题相关的信息。\n\n"
                f"您可以尝试问我以下证书的相关问题：\n{cert_names}\n\n"
                f"例如：\"CET-4怎么报名？\"、\"计算机二级考什么？\"、\"教师资格证需要什么条件？\""
            )
        }
    )


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
