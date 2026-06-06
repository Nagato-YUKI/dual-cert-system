"""External API routes module (placeholder for edu system integration)."""

from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__)


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})
