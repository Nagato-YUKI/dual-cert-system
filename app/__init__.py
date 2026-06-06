"""Flask application factory module."""

import os
from typing import Optional

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Initialize extensions without binding to an app instance yet
db: SQLAlchemy = SQLAlchemy()
jwt: JWTManager = JWTManager()
cors: CORS = CORS()


def create_app(config_name: Optional[str] = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Optional configuration name. Defaults to None.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Load configuration from config module
    app.config.from_object("config.Config")

    # Ensure upload folder exists
    upload_folder = app.config.get("UPLOAD_FOLDER")
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)

    # Ensure data directory exists for SQLite
    data_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    # Register blueprints - views_bp first to avoid route conflicts with API blueprints
    from app.routes.views import views_bp
    app.register_blueprint(views_bp)

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.student import student_bp
    from app.routes.review import review_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(student_bp, url_prefix="/student")
    # review_bp routes merged into admin_bp to avoid conflicts
    # app.register_blueprint(review_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Create database tables and default data
    with app.app_context():
        db.create_all()
        _create_default_admin()

    return app


def _create_default_admin() -> None:
    """Create a default admin account if no admin exists."""
    # Import models here to avoid circular imports
    from app.models.user import User

    admin_exists = db.session.execute(
        db.select(User).filter_by(username="admin")
    ).scalar_one_or_none()

    if admin_exists is None:
        default_admin = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role="admin",
        )
        db.session.add(default_admin)
        db.session.commit()
