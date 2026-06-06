"""Review routes module (AI + human review)."""

import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models.registration import Registration
from app.models.review_log import ReviewLog
from app.routes.auth import admin_required
from app.services.ai_review import ai_review_registration
from app.services.sms_service import notify_registration_status

review_bp = Blueprint("review", __name__)


# ---------------------------------------------------------------------------
# List registrations pending review
# ---------------------------------------------------------------------------

@review_bp.route("/reviews", methods=["GET"])
@admin_required
def list_reviews():
    """List registrations pending or under review."""
    status = request.args.get("status", "pending")
    review_status = request.args.get("review_status")

    query = db.select(Registration)
    if status:
        query = query.filter_by(status=status)
    if review_status:
        query = query.filter_by(review_status=review_status)

    items = db.session.execute(query).scalars().all()
    return jsonify([_registration_to_dict(i) for i in items])


# ---------------------------------------------------------------------------
# AI Review (single)
# ---------------------------------------------------------------------------

@review_bp.route("/reviews/<int:reg_id>/ai", methods=["POST"])
@admin_required
def trigger_ai_review(reg_id: int):
    """Trigger AI review for a single registration."""
    reg = db.session.execute(
        db.select(Registration).filter_by(id=reg_id)
    ).scalar_one_or_none()
    if not reg:
        return jsonify({"msg": "Registration not found"}), 404

    result = ai_review_registration(reg)

    # Update registration
    reg.ai_review_result = json.dumps(result, ensure_ascii=False)
    reg.ai_review_score = result["score"]

    if result["score"] >= 80 and result["result"] == "approved":
        reg.review_status = "ai_reviewed"
        reg.status = "approved"
    else:
        reg.review_status = "ai_reviewed"

    # Log review
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


# ---------------------------------------------------------------------------
# Batch AI Review
# ---------------------------------------------------------------------------

@review_bp.route("/reviews/batch-ai", methods=["POST"])
@admin_required
def batch_ai_review():
    """Trigger AI review for multiple registrations."""
    data = request.get_json(silent=True) or {}
    reg_ids = data.get("ids", [])
    if not reg_ids:
        return jsonify({"msg": "No registration IDs provided"}), 400

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


# ---------------------------------------------------------------------------
# Human Review
# ---------------------------------------------------------------------------

@review_bp.route("/reviews/<int:reg_id>", methods=["PUT"])
@admin_required
def human_review(reg_id: int):
    """Human review a registration (approve / reject / need_more_info)."""
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

    identity = get_jwt_identity()
    reviewer_id = identity.get("id")

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

    # Send SMS notification if student has phone
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
