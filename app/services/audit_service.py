"""Audit service for operation logging."""

from functools import wraps

from flask import request
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models.operation_log import OperationLog


def log_operation(action: str, target_type: str, get_target_id=None, get_details=None):
    """Decorator to automatically log an operation.

    Args:
        action: Action name, e.g. 'create_exam', 'approve_registration'.
        target_type: Target entity type, e.g. 'exam', 'registration'.
        get_target_id: Callable to extract target_id from args/kwargs, or static int.
        get_details: Callable to extract details from args/kwargs/result, or static str.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)

            try:
                # Extract identity
                user_id = int(get_jwt_identity())
                # Check if user is admin or student
                from app.models.user import User
                from app.models.student import Student
                user = db.session.execute(
                    db.select(User).filter_by(id=user_id)
                ).scalar_one_or_none()
                student = db.session.execute(
                    db.select(Student).filter_by(id=user_id)
                ).scalar_one_or_none()
                student_id = user_id if student else None
                user_id = user_id if user else None

                # Extract target_id
                target_id = None
                if callable(get_target_id):
                    try:
                        target_id = get_target_id(*args, **kwargs)
                    except Exception:
                        pass
                elif isinstance(get_target_id, int):
                    target_id = get_target_id
                else:
                    # Try common patterns
                    target_id = kwargs.get("id") or kwargs.get("exam_id") or kwargs.get("reg_id")

                # Extract details
                details = None
                if callable(get_details):
                    try:
                        details = get_details(*args, **kwargs, result=result)
                    except Exception:
                        pass
                elif isinstance(get_details, str):
                    details = get_details

                log = OperationLog(
                    user_id=user_id,
                    student_id=student_id,
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    details=details,
                    ip_address=_get_client_ip(),
                    user_agent=request.headers.get("User-Agent", "")[:500],
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                # Never let logging break the main flow
                db.session.rollback()
                print(f"[Audit] Failed to log operation: {e}")

            return result

        return wrapper

    return decorator


def _get_client_ip() -> str:
    """Get client IP from request."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    if request.headers.get("X-Real-Ip"):
        return request.headers.get("X-Real-Ip")
    if request.remote_addr:
        return request.remote_addr
    return ""
