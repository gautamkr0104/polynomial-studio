"""
Polynomial Studio — Main Application

Run with: python app.py
Accessible at: http://127.0.0.1:5000
"""
import os
import sys
import logging
from datetime import datetime

from flask import Flask, render_template, jsonify

import config as cfg

# ── Logging Setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(cfg.LOG_DIR, "app.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("polynomial_studio")


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=os.path.join(cfg.BASE_DIR, "templates"),
        static_folder=os.path.join(cfg.BASE_DIR, "static"),
    )
    app.config["SECRET_KEY"] = cfg.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max

    # ── Register Blueprints ────────────────────────────────────
    from routes.graph import graph_bp
    from routes.render import render_bp

    app.register_blueprint(graph_bp)
    app.register_blueprint(render_bp)

    # ── Main Page ──────────────────────────────────────────────
    @app.route("/")
    def index():
        # Check if manim is available
        manim_available = False
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "manim", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            manim_available = result.returncode == 0
        except Exception:
            pass

        # Check if ffmpeg is available
        ffmpeg_available = False
        try:
            import subprocess
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, timeout=10,
            )
            ffmpeg_available = result.returncode == 0
        except Exception:
            pass

        return render_template(
            "index.html",
            manim_available=manim_available,
            ffmpeg_available=ffmpeg_available,
        )

    # ── System Status ──────────────────────────────────────────
    @app.route("/api/status", methods=["GET"])
    def system_status():
        """Check system dependencies and return status."""
        status = {
            "manim": False,
            "ffmpeg": False,
            "python_version": sys.version,
        }

        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "manim", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            status["manim"] = result.returncode == 0
            if status["manim"]:
                status["manim_version"] = result.stdout.strip().split("\n")[0] if result.stdout else "unknown"
        except Exception:
            pass

        try:
            import subprocess
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, timeout=10,
            )
            status["ffmpeg"] = result.returncode == 0
        except Exception:
            pass

        return jsonify(status)

    # ── Error Handlers ─────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "Request too large"}), 413

    logger.info("=" * 50)
    logger.info("  Polynomial Studio started")
    logger.info(f"  http://127.0.0.1:5000")
    logger.info("=" * 50)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)
