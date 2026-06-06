"""Authentication routes module."""

from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
)
from werkzeug.security import check_password_hash

from app import db
from app.models.student import Student
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


def admin_required(fn):
    """Decorator to require admin role."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = db.session.execute(
            db.select(User).filter_by(id=user_id)
        ).scalar_one_or_none()
        if not user or user.role != "admin":
            return jsonify({"msg": "需要管理员权限"}), 403
        return fn(*args, **kwargs)

    return wrapper


def student_required(fn):
    """Decorator to require student role."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        student = db.session.execute(
            db.select(Student).filter_by(id=user_id)
        ).scalar_one_or_none()
        if not student:
            return jsonify({"msg": "需要学生权限"}), 403
        return fn(*args, **kwargs)

    return wrapper


@auth_bp.route("/login", methods=["POST"])
def admin_login():
    """Admin login endpoint."""
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "请输入用户名和密码"}), 400

    user = db.session.execute(
        db.select(User).filter_by(username=username)
    ).scalar_one_or_none()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"msg": "用户名或密码错误"}), 401

    access_token = create_access_token(
        identity=str(user.id)
    )
    avatar_url = (
        f"https://api.dicebear.com/10.x/bottts/svg?seed={user.name}"
    )
    return jsonify({
        "access_token": access_token,
        "role": "admin",
        "username": user.username,
        "name": user.name,
        "avatar_url": avatar_url,
    })


@auth_bp.route("/student/login", methods=["POST"])
def student_login():
    """Student login endpoint (student_no + id_card last 6 digits)."""
    data = request.get_json(silent=True) or {}
    student_no = data.get("student_no")
    password = data.get("password")

    if not student_no or not password:
        return jsonify({"msg": "请输入学号和密码"}), 400

    student = db.session.execute(
        db.select(Student).filter_by(student_no=student_no)
    ).scalar_one_or_none()

    if not student:
        return jsonify({"msg": "该学号不存在"}), 401

    # Use last 6 digits of id_card as default password
    expected = (student.id_card or "")[-6:] if student.id_card else ""
    if password != expected:
        return jsonify({"msg": "密码错误，请输入身份证后6位"}), 401

    access_token = create_access_token(
        identity=str(student.id)
    )

    # Auto-generate avatar URL using DiceBear API if not set
    if not student.avatar_url:
        student.avatar_url = (
            f"https://api.dicebear.com/10.x/lorelei/svg?seed={student.name}"
        )
        db.session.commit()

    return jsonify({
        "access_token": access_token,
        "role": "student",
        "student_no": student.student_no,
        "name": student.name,
        "avatar_url": student.avatar_url,
    })


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    """Get current user info."""
    user_id = int(get_jwt_identity())

    # Try admin first
    user = db.session.execute(
        db.select(User).filter_by(id=user_id)
    ).scalar_one_or_none()
    if user:
        avatar_url = (
            f"https://api.dicebear.com/10.x/bottts/svg?seed={user.name}"
        )
        return jsonify({
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "name": user.name,
            "avatar_url": avatar_url,
        })

    # Try student
    student = db.session.execute(
        db.select(Student).filter_by(id=user_id)
    ).scalar_one_or_none()
    if student:
        return jsonify({
            "id": student.id,
            "student_no": student.student_no,
            "name": student.name,
            "role": "student",
            "avatar_url": student.avatar_url,
        })

    return jsonify({"msg": "User not found"}), 404
