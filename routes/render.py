"""
Polynomial Studio — Render Routes

API endpoints for submitting render jobs, polling status, and serving videos.
"""
import os
from flask import Blueprint, request, jsonify, send_file, current_app

import config as cfg
from services.polynomial_parser import parse_polynomial
from services.render_manager import render_manager

render_bp = Blueprint("render", __name__)


@render_bp.route("/api/render", methods=["POST"])
def submit_render():
    """
    Submit a Manim rendering job.
    Expects JSON with:
        - equations: list of equation strings
        - colors: list of hex color strings
        - thicknesses: list of stroke widths
        - opacities: list of opacities
        - quality: quality preset key (e.g. "instagram_reel")
        - theme: theme key (e.g. "neon")
        - animation_options: dict of animation settings
    """
    data = request.get_json(silent=True)
    if not data or "equations" not in data:
        return jsonify({"success": False, "error": "No equations provided."}), 400

    equations = data["equations"]
    if not isinstance(equations, list):
        equations = [equations]

    if len(equations) > cfg.MAX_POLYNOMIALS:
        return jsonify({"success": False, "error": f"Maximum {cfg.MAX_POLYNOMIALS} polynomials allowed."}), 400

    # Parse and validate all polynomials
    poly_data = []
    colors_list = data.get("colors", [])
    thicknesses = data.get("thicknesses", [])
    opacities_list = data.get("opacities", [])

    for i, eq_str in enumerate(equations):
        parsed = parse_polynomial(eq_str)
        if not parsed["success"]:
            return jsonify({
                "success": False,
                "error": f"Invalid polynomial '{eq_str}': {parsed['error']}",
            }), 400

        poly_data.append({
            "expression_str": parsed["polynomial_str"],
            "latex": parsed["latex"],
            "color": colors_list[i] if i < len(colors_list) else "#00e5ff",
            "thickness": thicknesses[i] if i < len(thicknesses) else 4,
            "opacity": opacities_list[i] if i < len(opacities_list) else 1.0,
            "is_implicit": parsed.get("is_implicit", False),
            "implicit_expr": parsed.get("implicit_expr"),
        })

    # Get render config from quality preset
    quality_key = data.get("quality", "instagram_reel")
    if quality_key not in cfg.QUALITY_PRESETS:
        quality_key = "instagram_reel"
    render_config = cfg.QUALITY_PRESETS[quality_key].copy()

    # Get theme
    theme_key = data.get("theme", "neon")
    if theme_key not in cfg.ANIMATION_THEMES:
        theme_key = "neon"
    theme = cfg.ANIMATION_THEMES[theme_key]

    # Animation options
    animation_options = data.get("animation_options", {
        "show_roots": True,
        "show_extrema": True,
        "show_y_intercept": True,
        "show_equation": True,
        "explain_mode": False,
        "draw_speed": 2.0,
        "show_labels": True,
        "sequential": False,
    })

    # Submit render job
    job_id = render_manager.submit_job(
        polynomials=poly_data,
        render_config=render_config,
        theme=theme,
        animation_options=animation_options,
        output_video_dir=cfg.VIDEO_DIR,
        scene_dir=cfg.SCENE_TEMP_DIR,
    )

    return jsonify({
        "success": True,
        "job_id": job_id,
        "message": "Rendering job submitted.",
    })


@render_bp.route("/api/render-status/<job_id>", methods=["GET"])
def render_status(job_id):
    """Poll the status of a render job."""
    status = render_manager.get_job_status(job_id)
    if status is None:
        return jsonify({"success": False, "error": "Job not found."}), 404
    return jsonify({"success": True, "status": status})


@render_bp.route("/api/video/<filename>", methods=["GET"])
def serve_video(filename):
    """Serve a rendered video file."""
    # Sanitize filename to prevent path traversal
    safe_name = os.path.basename(filename)
    video_path = os.path.join(cfg.VIDEO_DIR, safe_name)

    if not os.path.isfile(video_path):
        return jsonify({"error": "Video not found."}), 404

    return send_file(
        video_path,
        mimetype="video/mp4",
        as_attachment=False,
    )


@render_bp.route("/api/video-download/<filename>", methods=["GET"])
def download_video(filename):
    """Download a rendered video file."""
    safe_name = os.path.basename(filename)
    video_path = os.path.join(cfg.VIDEO_DIR, safe_name)

    if not os.path.isfile(video_path):
        return jsonify({"error": "Video not found."}), 404

    from datetime import datetime
    download_name = f"polynomial_animation_{datetime.now().strftime('%Y-%m-%d')}.mp4"

    return send_file(
        video_path,
        mimetype="video/mp4",
        as_attachment=True,
        download_name=download_name,
    )


@render_bp.route("/api/themes", methods=["GET"])
def get_themes():
    """Return available animation themes."""
    themes = {}
    for key, theme in cfg.ANIMATION_THEMES.items():
        themes[key] = {
            "label": theme["label"],
            "background": theme["background"],
            "curve_primary": theme["curve_primary"],
            "curve_secondary": theme["curve_secondary"],
            "accent": theme["accent"],
            "description": theme["description"],
        }
    return jsonify({"themes": themes})


@render_bp.route("/api/quality-presets", methods=["GET"])
def get_quality_presets():
    """Return available quality presets."""
    presets = {}
    for key, preset in cfg.QUALITY_PRESETS.items():
        presets[key] = {
            "label": preset["label"],
            "width": preset["width"],
            "height": preset["height"],
            "fps": preset["fps"],
        }
    return jsonify({"presets": presets})
