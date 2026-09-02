"""
Polynomial Studio — Graph Routes

API endpoints for validation, analysis, and graph preview.
"""
from flask import Blueprint, request, jsonify
import sympy as sp
import numpy as np

from services.polynomial_parser import parse_polynomial
from services.polynomial_analyzer import analyze_polynomial, compute_graph_data, compute_graph_data_implicit

graph_bp = Blueprint("graph", __name__)

x = sp.Symbol("x")


@graph_bp.route("/api/validate", methods=["POST"])
def validate_equation():
    """Validate a single polynomial equation string."""
    data = request.get_json(silent=True)
    if not data or "equation" not in data:
        return jsonify({"success": False, "error": "No equation provided."}), 400

    result = parse_polynomial(data["equation"])

    if result["success"]:
        return jsonify({
            "success": True,
            "latex": result["latex"],
            "polynomial_str": result["polynomial_str"],
            "degree": result["degree"],
            "coefficients": result["coefficients"],
        })
    else:
        return jsonify({
            "success": False,
            "error": result["error"],
        }), 400


@graph_bp.route("/api/analyze", methods=["POST"])
def analyze():
    """Analyze one or more polynomials and return comprehensive math info."""
    data = request.get_json(silent=True)
    if not data or "equations" not in data:
        return jsonify({"success": False, "error": "No equations provided."}), 400

    equations = data["equations"]
    if not isinstance(equations, list):
        equations = [equations]

    if len(equations) > 5:
        return jsonify({"success": False, "error": "Maximum 5 polynomials allowed."}), 400

    results = []
    for eq_str in equations:
        parsed = parse_polynomial(eq_str)
        if not parsed["success"]:
            results.append({
                "equation": eq_str,
                "success": False,
                "error": parsed["error"],
            })
            continue

        analysis = analyze_polynomial(parsed["expression"])
        results.append({
            "equation": eq_str,
            "success": True,
            "latex": parsed["latex"],
            "polynomial_str": parsed["polynomial_str"],
            "degree": parsed["degree"],
            "coefficients": parsed["coefficients"],
            "analysis": analysis,
        })

    return jsonify({"success": True, "results": results})


@graph_bp.route("/api/preview", methods=["POST"])
def preview():
    """Generate graph data points for browser preview."""
    data = request.get_json(silent=True)
    if not data or "equations" not in data:
        return jsonify({"success": False, "error": "No equations provided."}), 400

    equations = data["equations"]
    if not isinstance(equations, list):
        equations = [equations]

    x_min = float(data.get("x_min", -6))
    x_max = float(data.get("x_max", 6))
    y_min = float(data.get("y_min", -6))
    y_max = float(data.get("y_max", 6))
    colors = data.get("colors", ["#00e5ff", "#e040fb", "#ff4081", "#7c4dff", "#ffab40"])
    thicknesses = data.get("thicknesses", [3, 3, 3, 3, 3])
    opacities = data.get("opacities", [1.0, 1.0, 1.0, 1.0, 1.0])

    series = []
    for i, eq_str in enumerate(equations):
        parsed = parse_polynomial(eq_str)
        if not parsed["success"]:
            continue

        color = colors[i % len(colors)] if i < len(colors) else colors[0]
        thickness = thicknesses[i] if i < len(thicknesses) else 3
        opacity = opacities[i] if i < len(opacities) else 1.0

        if parsed.get("is_implicit") and parsed.get("implicit_expr") is not None:
            # Implicit equation: use contour plotting
            graph_data = compute_graph_data_implicit(
                parsed["implicit_expr"], x_min, x_max, y_min, y_max, num_points=400
            )
            series.append({
                "type": "implicit",
                "segments_x": graph_data.get("segments_x", []),
                "segments_y": graph_data.get("segments_y", []),
                "latex": parsed["latex"],
                "color": color,
                "thickness": thickness,
                "opacity": opacity,
            })
        else:
            # Explicit equation: standard line plot
            graph_data = compute_graph_data(parsed["expression"], x_min, x_max, num_points=600)

            # Downsample for browser if needed (every 2nd point)
            x_vals = graph_data["x"][::2]
            y_vals = graph_data["y"][::2]

            series.append({
                "type": "explicit",
                "x": x_vals,
                "y": y_vals,
                "latex": parsed["latex"],
                "color": color,
                "thickness": thickness,
                "opacity": opacity,
                "y_min_auto": graph_data.get("y_min", -5),
                "y_max_auto": graph_data.get("y_max", 5),
            })

    # Compute overall y range
    all_y_min = -5
    all_y_max = 5
    if series:
        explicit_series = [s for s in series if s.get("type") == "explicit"]
        if explicit_series:
            all_y_min = min(s["y_min_auto"] for s in explicit_series)
            all_y_max = max(s["y_max_auto"] for s in explicit_series)

    return jsonify({
        "success": True,
        "series": series,
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min if any(s.get("type") == "implicit" for s in series) else all_y_min,
        "y_max": y_max if any(s.get("type") == "implicit" for s in series) else all_y_max,
    })
