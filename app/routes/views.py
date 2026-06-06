"""Template view routes."""

from flask import Blueprint, render_template

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    """Redirect to login page."""
    return render_template("login.html")


@views_bp.route("/login")
def login_page():
    """Login page."""
    return render_template("login.html")


@views_bp.route("/admin")
def admin_dashboard():
    """Admin dashboard page."""
    return render_template("admin/dashboard.html")


@views_bp.route("/admin/certificates")
def admin_certificates():
    """Admin certificate management page."""
    return render_template("admin/certificates.html")


@views_bp.route("/admin/exams")
def admin_exams():
    """Admin exam management page."""
    return render_template("admin/exams.html")


@views_bp.route("/admin/reviews")
def admin_reviews():
    """Admin review center page."""
    return render_template("admin/reviews.html")


@views_bp.route("/student")
def student_dashboard():
    """Student dashboard page."""
    return render_template("student/dashboard.html")


@views_bp.route("/student/certificates")
def student_certificates():
    """Student certificate browse page."""
    return render_template("student/certificates.html")


@views_bp.route("/student/exams")
def student_exams():
    """Student exam registration page."""
    return render_template("student/exams.html")


@views_bp.route("/admin/bigscreen")
def admin_bigscreen():
    """Admin data big screen page."""
    return render_template("admin/bigscreen.html")
