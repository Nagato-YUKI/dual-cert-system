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
        identity = get_jwt_identity()
        if identity.get("role") != "admin":
            return jsonify({"msg": "Admin access required"}), 403
        return fn(*args, **kwargs)

    return wrapper


def student_required(fn):
    """Decorator to require student role."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if identity.get("role") != "student":
            return jsonify({"msg": "Student access required"}), 403
        return fn(*args, **kwargs)

    return wrapper


@auth_bp.route("/login", methods=["POST"])
def admin_login():
    """Admin login endpoint."""
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400

    user = db.session.execute(
        db.select(User).filter_by(username=username)
    ).scalar_one_or_none()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Invalid username or password"}), 401

    access_token = create_access_token(
        identity={"id": user.id, "role": "admin", "username": user.username}
    )
    return jsonify({
        "access_token": access_token,
        "role": "admin",
        "username": user.username,
        "name": user.name,
    })


@auth_bp.route("/student/login", methods=["POST"])
def student_login():
    """Student login endpoint (student_no + id_card last 6 digits)."""
    data = request.get_json(silent=True) or {}
    student_no = data.get("student_no")
    password = data.get("password")

    if not student_no or not password:
        return jsonify({"msg": "Student number and password are required"}), 400

    student = db.session.execute(
        db.select(Student).filter_by(student_no=student_no)
    ).scalar_one_or_none()

    if not student:
        return jsonify({"msg": "Student not found"}), 401

    # Use last 6 digits of id_card as default password
    expected = (student.id_card or "")[-6:] if student.id_card else ""
    if password != expected:
        return jsonify({"msg": "Invalid password"}), 401

    access_token = create_access_token(
        identity={
            "id": student.id,
            "role": "student",
            "student_no": student.student_no,
            "name": student.name,
        }
    )
    return jsonify({
        "access_token": access_token,
        "role": "student",
        "student_no": student.student_no,
        "name": student.name,
    })


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    """Get current user info."""
    identity = get_jwt_identity()
    role = identity.get("role")

    if role == "admin":
        user = db.session.execute(
            db.select(User).filter_by(id=identity["id"])
        ).scalar_one_or_none()
        if not user:
            return jsonify({"msg": "User not found"}), 404
        return jsonify({
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "name": user.name,
        })

    if role == "student":
        student = db.session.execute(
            db.select(Student).filter_by(id=identity["id"])
        ).scalar_one_or_none()
        if not student:
            return jsonify({"msg": "Student not found"}), 404
        return jsonify({
            "id": student.id,
            "student_no": student.student_no,
            "name": student.name,
            "role": "student",
        })

    return jsonify({"msg": "Unknown role"}), 400
