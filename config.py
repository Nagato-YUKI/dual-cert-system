"""Application configuration module."""

import os

from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration class."""

    # Security keys
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production")

    # Database - PostgreSQL required
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    @classmethod
    def validate(cls) -> None:
        """Validate that required configs are set."""
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY environment变量必填")
        if not cls.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY 环境变量必填")
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL 环境变量必填（PostgreSQL）")
