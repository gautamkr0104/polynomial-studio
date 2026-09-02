"""
Polynomial Studio — Manim Scene Generator

Dynamically generates Manim animation scenes with auto-following tracer dot,
trail effects, coordinate readouts, and auto-pulsing mathematical highlights.
Never executes raw user code.
"""
import os
import sys
import json
import uuid
import time
import subprocess
import logging
import sympy as sp
from datetime import datetime

logger = logging.getLogger("polynomial_studio")

x = sp.Symbol("x")


def _hex_to_manim_color(hex_color: str) -> str:
    """Convert a hex color string to a Manim-compatible color constant or hex."""
    hex_color = hex_color.strip().lstrip("#")
    return f"#{hex_color}"


def _build_color_dict(theme: dict) -> dict:
    """Convert theme dict to Manim-compatible color values."""
    return {
        "bg": _hex_to_manim_color(theme.get("background", "#0a0a1a")),
        "curve_primary": _hex_to_manim_color(theme.get("curve_primary", "#00e5ff")),
        "curve_secondary": _hex_to_manim_color(theme.get("curve_secondary", "#e040fb")),
        "accent": _hex_to_manim_color(theme.get("accent", "#7c4dff")),
        "grid": _hex_to_manim_color(theme.get("grid", "#1a1a3e")),
        "text": _hex_to_manim_color(theme.get("text", "#e0e0e0")),
        "root_color": _hex_to_manim_color(theme.get("root_color", "#ff4081")),
        "glow": theme.get("glow", False),
    }


def _compute_implicit_contour(implicit_expr, x_min=-6, x_max=6, y_min=-6, y_max=6, num_points=400):
    """Compute contour segments for an implicit equation F(x,y) = 0 using matplotlib."""
    import numpy as np
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        x_sym, y_sym = sp.symbols("x y")
        x_arr = np.linspace(x_min, x_max, num_points)
        y_arr = np.linspace(y_min, y_max, num_points)
        X, Y = np.meshgrid(x_arr, y_arr)

        f = sp.lambdify((x_sym, y_sym), implicit_expr, modules=["numpy"])
        Z = f(X, Y)
        Z = np.where(np.isfinite(Z), Z, np.nan)

        fig, ax = plt.subplots()
        cs = ax.contour(X, Y, Z, levels=[0])
        plt.close(fig)

        segments_x = []
        segments_y = []
        if hasattr(cs, 'allsegs') and cs.allsegs:
            for level_segs in cs.allsegs:
                for seg in level_segs:
                    if len(seg) > 1:
                        segments_x.append(seg[:, 0].tolist())
                        segments_y.append(seg[:, 1].tolist())
        elif hasattr(cs, 'collections'):
            for collection in cs.collections:
                for p in collection.get_paths():
                    vertices = p.vertices
                    if len(vertices) > 1:
                        segments_x.append(vertices[:, 0].tolist())
                        segments_y.append(vertices[:, 1].tolist())

        return {"segments_x": segments_x, "segments_y": segments_y}
    except Exception as e:
        logger.warning(f"Implicit contour computation failed: {e}")
        return {"segments_x": [], "segments_y": []}


def generate_manim_scene(
    polynomials: list[dict],
    render_config: dict,
    theme: dict,
    animation_options: dict,
    output_dir: str,
) -> str:
    """
    Generate a Manim scene Python file from validated polynomial data.

    Returns:
        Path to the generated .py scene file
    """
    colors = _build_color_dict(theme)
    w = render_config.get("width", 1920)
    h = render_config.get("height", 1080)

    # Pre-compute contour data for implicit polynomials
    contour_data = {}
    for i, poly in enumerate(polynomials):
        if poly.get("is_implicit") and poly.get("implicit_expr") is not None:
            contour = _compute_implicit_contour(poly["implicit_expr"])
            contour_data[i] = contour

    poly_lines = []
    for i, poly in enumerate(polynomials):
        poly_lines.append({
            "index": i,
            "expr_str": poly["expression_str"],
            "color": _hex_to_manim_color(poly.get("color", colors["curve_primary"])),
            "thickness": poly.get("thickness", 4),
            "opacity": poly.get("opacity", 1.0),
            "latex": poly.get("latex", ""),
            "is_implicit": poly.get("is_implicit", False),
        })

    show_roots = animation_options.get("show_roots", True)
    show_extrema = animation_options.get("show_extrema", True)
    show_y_intercept = animation_options.get("show_y_intercept", True)
    show_equation = animation_options.get("show_equation", True)
    explain_mode = animation_options.get("explain_mode", False)
    draw_speed = animation_options.get("draw_speed", 2.0)
    show_labels = animation_options.get("show_labels", True)
    sequential = animation_options.get("sequential", False)

    scene_id = f"scene_{uuid.uuid4().hex[:8]}"
    scene_filename = f"{scene_id}.py"
    scene_path = os.path.join(output_dir, scene_filename)

    source = _build_scene_source(
        poly_lines=poly_lines,
        colors=colors,
        w=w, h=h,
        show_roots=show_roots,
        show_extrema=show_extrema,
        show_y_intercept=show_y_intercept,
        show_equation=show_equation,
        explain_mode=explain_mode,
        draw_speed=draw_speed,
        show_labels=show_labels,
        sequential=sequential,
        scene_id=scene_id,
        contour_data=contour_data,
    )

    with open(scene_path, "w", encoding="utf-8") as f:
        f.write(source)

    logger.info(f"Generated Manim scene: {scene_path}")
    return scene_path


def _build_scene_source(
    poly_lines, colors, w, h,
    show_roots, show_extrema, show_y_intercept, show_equation,
    explain_mode, draw_speed, show_labels, sequential, scene_id,
    contour_data=None,
):
    """
    Build complete Manim scene source with auto-following tracer dot animation.
    Uses string concatenation (not f-strings) to avoid brace-escaping issues.
    """
    poly_specs = []
    for p in poly_lines:
        poly_specs.append({
            "expr_str": p["expr_str"],
            "color": p["color"],
            "stroke_width": p["thickness"],
            "stroke_opacity": p["opacity"],
            "latex": p["latex"],
            "is_implicit": p.get("is_implicit", False),
        })

    # JSON-safe embedding
    poly_specs_json = json.dumps(poly_specs)
    contour_data_json = json.dumps(contour_data or {})

    # Build source using string concatenation to avoid f-string brace issues
    source = (
        '"""\n'
        'Auto-generated Manim scene for Polynomial Studio.\n'
        'Scene ID: ' + scene_id + '\n'
        'Generated: ' + datetime.now().isoformat() + '\n'
        '"""\n'
        'import json\n'
        'import numpy as np\n'
        'import sympy as sp\n'
        'from manim import *\n'
        '\n'
        '# ── Configuration ──────────────────────────────────────────────\n'
        'POLY_SPECS = json.loads(' + repr(poly_specs_json) + ')\n'
        'CONTOUR_DATA = json.loads(' + repr(contour_data_json) + ')\n'
        '\n'
        'THEME_BG = "' + colors["bg"] + '"\n'
        'THEME_CURVE_PRIMARY = "' + colors["curve_primary"] + '"\n'
        'THEME_GRID = "' + colors["grid"] + '"\n'
        'THEME_TEXT = "' + colors["text"] + '"\n'
        'THEME_ROOT_COLOR = "' + colors["root_color"] + '"\n'
        'THEME_ACCENT = "' + colors["accent"] + '"\n'
        'THEME_GLOW = ' + str(colors["glow"]) + '\n'
        '\n'
        'SHOW_ROOTS = ' + str(show_roots) + '\n'
        'SHOW_EXTREMA = ' + str(show_extrema) + '\n'
        'SHOW_Y_INTERCEPT = ' + str(show_y_intercept) + '\n'
        'SHOW_EQUATION = ' + str(show_equation) + '\n'
        'EXPLAIN_MODE = ' + str(explain_mode) + '\n'
        'DRAW_SPEED = ' + str(draw_speed) + '\n'
        'SHOW_LABELS = ' + str(show_labels) + '\n'
        'SEQUENTIAL_DRAW = ' + str(sequential) + '\n'
        '\n'
        'FRAME_WIDTH = ' + str(w) + '\n'
        'FRAME_HEIGHT = ' + str(h) + '\n'
        '\n'
        '\n'
        'def _make_curve(spec, axes, x_lo, x_hi, idx):\n'
        '    """Build a curve from a polynomial spec.\n'
        '    For implicit curves, draw pre-computed contour segments.\n'
        '    For explicit curves, use ParametricFunction."""\n'
        '    if spec.get("is_implicit") and idx in CONTOUR_DATA:\n'
        '        contour = CONTOUR_DATA[idx]\n'
        '        segs_x = contour.get("segments_x", [])\n'
        '        segs_y = contour.get("segments_y", [])\n'
        '        group = VGroup()\n'
        '        for sx, sy in zip(segs_x, segs_y):\n'
        '            points = [axes.c2p(px, py) for px, py in zip(sx, sy)]\n'
        '            if len(points) >= 2:\n'
        '                path = VMobject(\n'
        '                    color=spec["color"],\n'
        '                    stroke_width=spec.get("stroke_width", 4),\n'
        '                    stroke_opacity=spec.get("stroke_opacity", 1.0),\n'
        '                )\n'
        '                path.set_points_as_corners(points)\n'
        '                group.add(path)\n'
        '        if len(group) == 0:\n'
        '            group.add(Dot(axes.c2p(0, 0), radius=0, opacity=0))\n'
        '        return group, None\n'
        '    # Also check contour data even if is_implicit flag is not set\n'

        '    if idx in CONTOUR_DATA:\n'
        '        contour = CONTOUR_DATA[idx]\n'
        '        segs_x = contour.get("segments_x", [])\n'
        '        segs_y = contour.get("segments_y", [])\n'
        '        if segs_x and segs_y:\n'
        '            group = VGroup()\n'
        '            for sx, sy in zip(segs_x, segs_y):\n'
        '                points = [axes.c2p(px, py) for px, py in zip(sx, sy)]\n'
        '                if len(points) >= 2:\n'
        '                    path = VMobject(\n'
        '                        color=spec["color"],\n'
        '                        stroke_width=spec.get("stroke_width", 4),\n'
        '                        stroke_opacity=spec.get("stroke_opacity", 1.0),\n'
        '                    )\n'
        '                    path.set_points_as_corners(points)\n'
        '                    group.add(path)\n'
        '            if len(group) > 0:\n'
        '                return group, None\n'
        '    expr = sp.sympify(spec["expr_str"])\n'
        '    f = sp.lambdify(sp.Symbol("x"), expr, modules=["numpy"])\n'
        '    def param_func(t):\n'
        '        try:\n'
        '            y_val = float(f(t))\n'
        '        except (TypeError, ValueError):\n'
        '            y_val = 0.0\n'
        '        if not np.isfinite(y_val):\n'
        '            y_val = 0.0\n'
        '        return axes.c2p(t, y_val)\n'
        '    curve = ParametricFunction(\n'
        '        param_func,\n'
        '        t_range=[x_lo, x_hi, 0.005],\n'
        '        color=spec["color"],\n'
        '        stroke_width=spec.get("stroke_width", 4),\n'
        '        stroke_opacity=spec.get("stroke_opacity", 1.0),\n'
        '    )\n'
        '    return curve, f\n'
        '\n'
        '\n'
        'def _lerp_color(c1, c2, t):\n'
        '    """Linearly interpolate between two Manim colors."""\n'
        '    r1, g1, b1 = hex_to_rgb(c1)\n'
        '    r2, g2, b2 = hex_to_rgb(c2)\n'
        '    return rgb_to_hex([\n'
        '        r1 + (r2 - r1) * t,\n'
        '        g1 + (g2 - g1) * t,\n'
        '        b1 + (b2 - b1) * t,\n'
        '    ])\n'
        '\n'
        '\n'
        'class PolynomialScene(Scene):\n'
        '    def setup(self):\n'
        '        self.camera.background_color = THEME_BG\n'
        '\n'
        '    def construct(self):\n'
        '        font_scale = max(min(FRAME_WIDTH, FRAME_HEIGHT) / 1080, 0.5)\n'
        '\n'
        '        # ── Compute axis range ─────────────────────────────────\n'
        '        x_min, x_max = -6, 6\n'
        '        y_min, y_max = -6, 6\n'
        '        all_y = []\n'
        '        for spec in POLY_SPECS:\n'
        '            if spec.get("is_implicit"):\n'
        '                continue\n'
        '            expr = sp.sympify(spec["expr_str"])\n'
        '            f = sp.lambdify(sp.Symbol("x"), expr, modules=["numpy"])\n'
        '            xs = np.linspace(x_min, x_max, 400)\n'
        '            try:\n'
        '                ys = f(xs)\n'
        '                valid = ys[np.isfinite(ys)]\n'
        '                if len(valid) > 0:\n'
        '                    all_y.extend(valid.tolist())\n'
        '            except Exception:\n'
        '                pass\n'
        '        if all_y:\n'
        '            y_arr = np.array(all_y)\n'
        '            y_p5 = float(np.percentile(y_arr, 5))\n'
        '            y_p95 = float(np.percentile(y_arr, 95))\n'
        '            y_range = y_p95 - y_p5\n'
        '            if y_range < 0.1:\n'
        '                y_range = 4\n'
        '            y_min = y_p5 - y_range * 0.25\n'
        '            y_max = y_p95 + y_range * 0.25\n'
        '        y_min = round(y_min, 1) - 0.5\n'
        '        y_max = round(y_max, 1) + 0.5\n'
        '        x_step = 1\n'
        '        y_step = 1\n'
        '        if (x_max - x_min) > 15:\n'
        '            x_step = 2\n'
        '        if (y_max - y_min) > 15:\n'
        '            y_step = 2\n'
        '\n'
        '        # ── Scene 1: Opening (Explain Mode) ─────────────────────\n'
        '        if EXPLAIN_MODE:\n'
        '            title = Text(\n'
        '                "Polynomial Studio",\n'
        '                font_size=int(48 * font_scale),\n'
        '                color=THEME_TEXT,\n'
        '            )\n'
        '            subtitle = Text(\n'
        '                "Visualize \\u00b7 Analyze \\u00b7 Animate",\n'
        '                font_size=int(24 * font_scale),\n'
        '                color=THEME_TEXT,\n'
        '                opacity=0.7,\n'
        '            )\n'
        '            subtitle.next_to(title, DOWN, buff=0.3)\n'
        '            self.play(\n'
        '                FadeIn(title, shift=UP * 0.3),\n'
        '                FadeIn(subtitle, shift=UP * 0.3),\n'
        '                run_time=1.2,\n'
        '            )\n'
        '            self.wait(1)\n'
        '            self.play(FadeOut(title), FadeOut(subtitle), run_time=0.6)\n'
        '\n'
        '        # ── Scene 2: Axes ──────────────────────────────────────\n'
        '        axes = Axes(\n'
        '            x_range=[x_min, x_max, x_step],\n'
        '            y_range=[y_min, y_max, y_step],\n'
        '            x_length=10,\n'
        '            y_length=6.5,\n'
        '            tips=True,\n'
        '            axis_config={\n'
        '                "color": THEME_TEXT,\n'
        '                "stroke_width": 2,\n'
        '                "include_numbers": False,\n'
        '                "font_size": int(20 * font_scale),\n'
        '            },\n'
        '        )\n'
        '        axes.set_z_index(1)\n'
        '        # Build grid lines manually (get_axis_grid removed in Manim 0.21)\n'
        '        grid = VGroup()\n'
        '        for x_val in np.arange(x_min, x_max + x_step, x_step):\n'
        '            start = axes.c2p(x_val, y_min)\n'
        '            end = axes.c2p(x_val, y_max)\n'
        '            grid.add(Line(start, end, color=THEME_GRID, stroke_width=1, stroke_opacity=0.4))\n'
        '        for y_val in np.arange(y_min, y_max + y_step, y_step):\n'
        '            start = axes.c2p(x_min, y_val)\n'
        '            end = axes.c2p(x_max, y_val)\n'
        '            grid.add(Line(start, end, color=THEME_GRID, stroke_width=1, stroke_opacity=0.4))\n'
        '        x_axis = axes.x_axis\n'
        '        y_axis = axes.y_axis\n'
        '        x_label = Text("x", font_size=int(24 * font_scale), color=THEME_TEXT)\n'
        '        y_label = Text("y", font_size=int(24 * font_scale), color=THEME_TEXT)\n'
        '        x_label.next_to(x_axis.get_end(), DOWN, buff=0.15)\n'
        '        y_label.next_to(y_axis.get_end(), LEFT, buff=0.15)\n'
        '        self.play(Create(axes), run_time=1.5)\n'
        '        self.play(FadeIn(grid), run_time=0.8)\n'
        '        self.play(FadeIn(x_label), FadeIn(y_label), run_time=0.5)\n'
        '        if EXPLAIN_MODE:\n'
        '            self.wait(0.5)\n'
        '\n'
        '        # ── Scene 3: Equation ──────────────────────────────────\n'
        '        equation_mobjects = []\n'
        '        if SHOW_EQUATION:\n'
        '            for spec in POLY_SPECS:\n'
        '                latex_str = spec.get("latex", "")\n'
        '                if latex_str:\n'
        '                    eq_text = MathTex(latex_str, font_size=int(24 * font_scale))\n'
        '                else:\n'
        '                    eq_text = Text(spec["expr_str"], font_size=int(24 * font_scale))\n'
        '                eq_text.set_color(THEME_TEXT)\n'
        '                equation_mobjects.append(eq_text)\n'
        '            if len(equation_mobjects) == 1:\n'
        '                equation_mobjects[0].to_edge(UP, buff=0.4)\n'
        '                self.play(Write(equation_mobjects[0]), run_time=1.2)\n'
        '            else:\n'
        '                eq_group = VGroup(*equation_mobjects).arrange(\n'
        '                    DOWN, buff=0.25\n'
        '                )\n'
        '                eq_group.to_edge(UP, buff=0.3)\n'
        '                self.play(Write(eq_group), run_time=1.5)\n'
        '\n'
        '        # ── Scene 4: Curve Construction with Tracer ────────────\n'
        '        graph_mobjects = []\n'
        '        graph_functions = []\n'
        '        all_draw_anims = []\n'
        '        all_tracer_dots = []\n'
        '        all_traces = []\n'
        '        all_guides = []\n'
        '        all_coord_texts = []\n'
        '\n'
        '        for i, spec in enumerate(POLY_SPECS):\n'
        '            curve, f = _make_curve(spec, axes, x_min, x_max, i)\n'
        '            color = spec["color"]\n'
        '            is_imp = spec.get("is_implicit", False)\n'
        '            graph_mobjects.append(curve)\n'
        '            if f is not None:\n'
        '                graph_functions.append((sp.sympify(spec["expr_str"]), f, color))\n'
        '\n'
        '            if is_imp:\n'
        '                # Implicit curves: simple fade-in, no tracer\n'
        '                all_draw_anims.append(None)\n'
        '                all_tracer_dots.append(None)\n'
        '                all_traces.append(None)\n'
        '                all_guides.append(None)\n'
        '                all_coord_texts.append(None)\n'
        '                continue\n'
        '\n'
        '            # ── Tracer dot ──────────────────────────────────\n'
        '            tracer = Dot(\n'
        '                curve.get_start(),\n'
        '                color=color,\n'
        '                radius=0.12,\n'
        '                z_index=10,\n'
        '            )\n'
        '            tracer_glow = Dot(\n'
        '                curve.get_start(),\n'
        '                color=color,\n'
        '                radius=0.22,\n'
        '                fill_opacity=0.25,\n'
        '                z_index=9,\n'
        '            )\n'
        '            tracer_group = VGroup(tracer_glow, tracer)\n'
        '\n'
        '            # ── Trail (TracedPath) ─────────────────────────\n'
        '            trace = TracedPath(\n'
        '                tracer.get_center,\n'
        '                stroke_color=color,\n'
        '                stroke_width=spec.get("stroke_width", 4) + 2,\n'
        '                stroke_opacity=0.35,\n'
        '            )\n'
        '\n'
        '            # ── Guide line (tracer to x-axis) ──────────────\n'
        '            guide_line = DashedLine(\n'
        '                tracer.get_center(),\n'
        '                axes.c2p(axes.p2c(tracer.get_center())[0], 0),\n'
        '                color=color,\n'
        '                stroke_width=1,\n'
        '                stroke_opacity=0.3,\n'
        '                dash_length=0.06,\n'
        '                z_index=2,\n'
        '            )\n'
        '\n'
        '            # ── Coordinate readout ─────────────────────────\n'
        '            coord_text = Text(\n'
        '                "", font_size=int(16 * font_scale), color=color\n'
        '            )\n'
        '            coord_text.set_z_index(10)\n'
        '\n'
        '            all_draw_anims.append((curve, tracer_group, trace, guide_line, coord_text))\n'
        '            all_tracer_dots.append((tracer, tracer_glow))\n'
        '            all_traces.append(trace)\n'
        '            all_guides.append(guide_line)\n'
        '            all_coord_texts.append(coord_text)\n'
        '\n'
        '        # ── Helper: coordinate readout updater ─────────────────\n'
        '        # NOTE: We only move the text, never recreate it —\n'
        '        # creating Text() per-frame is the #1 render bottleneck.\n'
        '        def _make_coord_updater(ct, tracer_m, axes_m):\n'
        '            def updater(mob):\n'
        '                try:\n'
        '                    mob.next_to(tracer_m, UP, buff=0.15)\n'
        '                except Exception:\n'
        '                    pass\n'
        '            return updater\n'
        '\n'
        '        # ── Helper: guide line updater ─────────────────────────\n'
        '        def _make_guide_updater(gl, tracer_m, axes_m):\n'
        '            def updater(mob):\n'
        '                try:\n'
        '                    cx, _ = axes_m.p2c(tracer_m.get_center())\n'
        '                    start = tracer_m.get_center()\n'
        '                    end = axes_m.c2p(cx, 0)\n'
        '                    mob.put_start_and_end_on(start, end)\n'
        '                except Exception:\n'
        '                    pass\n'
        '            return updater\n'
        '\n'
        '        # ── Collect all highlight points per curve ──────────────\n'
        '        highlight_data = {}\n'
        '        _gf_idx = 0\n'
        '        for _pi, _spec in enumerate(POLY_SPECS):\n'
        '            if _spec.get("is_implicit", False):\n'
        '                continue\n'
        '            if _gf_idx >= len(graph_functions):\n'
        '                break\n'
        '            expr, f, color = graph_functions[_gf_idx]\n'
        '            _gf_idx += 1\n'
        '            points = []\n'
        '            if SHOW_ROOTS:\n'
        '                try:\n'
        '                    real_roots = sp.real_roots(expr, sp.Symbol("x"))\n'
        '                    for r in real_roots:\n'
        '                        rv = float(r)\n'
        '                        if x_min <= rv <= x_max:\n'
        '                            fv = float(f(rv))\n'
        '                            if abs(fv) < 100:\n'
        '                                points.append({\n'
        '                                    "type": "root",\n'
        '                                    "x": rv, "y": 0.0,\n'
        '                                    "color": THEME_ROOT_COLOR,\n'
        '                                })\n'
        '                except Exception:\n'
        '                    pass\n'
        '            if SHOW_Y_INTERCEPT:\n'
        '                try:\n'
        '                    y_val = float(f(0))\n'
        '                    if x_min <= 0 <= x_max and abs(y_val) < 1000:\n'
        '                        points.append({\n'
        '                            "type": "y_intercept",\n'
        '                            "x": 0.0, "y": y_val,\n'
        '                            "color": THEME_ACCENT,\n'
        '                        })\n'
        '                except Exception:\n'
        '                    pass\n'
        '            if SHOW_EXTREMA:\n'
        '                try:\n'
        '                    deriv = sp.diff(expr, sp.Symbol("x"))\n'
        '                    crit = sp.solve(deriv, sp.Symbol("x"))\n'
        '                    d2 = sp.diff(deriv, sp.Symbol("x"))\n'
        '                    for cp in crit:\n'
        '                        if cp.is_real:\n'
        '                            cpv = float(cp)\n'
        '                            if x_min <= cpv <= x_max:\n'
        '                                fv = float(f(cpv))\n'
        '                                if abs(fv) < 1000:\n'
        '                                    d2v = float(d2.subs(sp.Symbol("x"), cpv))\n'
        '                                    ptype = "max" if d2v < 0 else "min"\n'
        '                                    points.append({\n'
        '                                        "type": ptype,\n'
        '                                        "x": cpv, "y": fv,\n'
        '                                        "color": color,\n'
        '                                    })\n'
        '                except Exception:\n'
        '                    pass\n'
        '            points.sort(key=lambda p: p["x"])\n'
        '            highlight_data[_pi] = points\n'
        '\n'
        '        # ── Run animation per curve ────────────────────────────\n'
        '        for idx, anim_entry in enumerate(all_draw_anims):\n'
        '            if anim_entry is None:\n'
        '                # Implicit curve: just fade in\n'
        '                curve = graph_mobjects[idx]\n'
        '                color = POLY_SPECS[idx]["color"]\n'
        '                self.play(Create(curve), run_time=DRAW_SPEED)\n'
        '                self.wait(0.3)\n'
        '                if SEQUENTIAL_DRAW and idx < len(all_draw_anims) - 1:\n'
        '                    self.wait(0.4)\n'
        '                continue\n'
        '\n'
        '            curve, tracer_grp, trace, guide, coord_txt = anim_entry\n'
        '            tracer, tracer_glow = all_tracer_dots[idx]\n'
        '            coord_updater = _make_coord_updater(coord_txt, tracer, axes)\n'
        '            guide_updater = _make_guide_updater(guide, tracer, axes)\n'
        '\n'
        '            # Fade in tracer\n'
        '            self.play(\n'
        '                FadeIn(tracer_grp, scale=3),\n'
        '                FadeIn(coord_txt),\n'
        '                run_time=0.4,\n'
        '            )\n'
        '            self.add(trace)\n'
        '\n'
        '            # ── Build combined draw animation ────────────────\n'
        '            draw_anims = [\n'
        '                Create(curve),\n'
        '                MoveAlongPath(tracer_grp, curve),\n'
        '                UpdateFromFunc(coord_txt, coord_updater),\n'
        '                UpdateFromFunc(guide, guide_updater),\n'
        '                FadeIn(guide),\n'
        '            ]\n'
        '\n'
        '            # Auto-pulse at key points while drawing\n'
        '            pts = highlight_data.get(idx, [])\n'
        '            pulse_anims = []\n'
        '            for pt in pts:\n'
        '                px = pt["x"]\n'
        '                flash = Dot(\n'
        '                    axes.c2p(px, pt["y"]),\n'
        '                    color=pt["color"],\n'
        '                    radius=0.06,\n'
        '                    fill_opacity=0.0,\n'
        '                    z_index=8,\n'
        '                )\n'
        '                pulse_anims.append((px, flash, pt))\n'
        '\n'
        '            # Draw the curve with tracer\n'
        '            self.play(*draw_anims, run_time=DRAW_SPEED)\n'
        '            self.remove(guide)\n'
        '\n'
        '            # ── Flash at each key point sequentially ──────────\n'
        '            for px, flash, pt in pulse_anims:\n'
        '                pt_label = None\n'
        '                if SHOW_LABELS:\n'
        '                    if pt["type"] == "root":\n'
        '                        pt_label = Text(\n'
        '                            f"x={sp.nsimplify(px)}",\n'
        '                            font_size=int(18 * font_scale),\n'
        '                            color=pt["color"],\n'
        '                        )\n'
        '                    elif pt["type"] == "y_intercept":\n'
        '                        pt_label = Text(\n'
        '                            f"(0, {round(pt[\'y\'], 2)})",\n'
        '                            font_size=int(16 * font_scale),\n'
        '                            color=pt["color"],\n'
        '                        )\n'
        '                    elif pt["type"] in ("max", "min"):\n'
        '                        pt_label = Text(\n'
        '                            f"({round(px, 2)}, {round(pt[\'y\'], 2)})",\n'
        '                            font_size=int(16 * font_scale),\n'
        '                            color=pt["color"],\n'
        '                        )\n'
        '                    if pt_label is not None:\n'
        '                        direction = UP if pt["type"] != "min" else DOWN\n'
        '                        pt_label.next_to(flash, direction, buff=0.12)\n'
        '\n'
        '                anims_flash = [\n'
        '                    Flash(\n'
        '                        flash,\n'
        '                        color=pt["color"],\n'
        '                        line_length=0.15,\n'
        '                        num_lines=6,\n'
        '                        run_time=0.4,\n'
        '                    ),\n'
        '                ]\n'
        '                if pt_label is not None:\n'
        '                    anims_flash.append(\n'
        '                        FadeIn(pt_label, shift=UP * 0.1, run_time=0.4)\n'
        '                    )\n'
        '                self.play(*anims_flash, run_time=0.5)\n'
        '                self.wait(0.15)\n'
        '\n'
        '            # ── End-of-curve pulse ─────────────────────────────\n'
        '            self.play(\n'
        '                tracer_glow.animate.scale(1.5).set_opacity(0.5),\n'
        '                run_time=0.3,\n'
        '            )\n'
        '            self.play(\n'
        '                tracer_glow.animate.scale(1 / 1.5).set_opacity(0.25),\n'
        '                run_time=0.3,\n'
        '            )\n'
        '            self.wait(0.3)\n'
        '\n'
        '            # Fade out tracer and trace\n'
        '            self.play(\n'
        '                FadeOut(tracer_grp),\n'
        '                FadeOut(coord_txt),\n'
        '                FadeOut(trace),\n'
        '                run_time=0.5,\n'
        '            )\n'
        '\n'
        '            if SEQUENTIAL_DRAW and idx < len(all_draw_anims) - 1:\n'
        '                self.wait(0.4)\n'
        '\n'
        '        self.wait(0.5)\n'
        '\n'
        '        # ── Scene 6: Final Hold ──────────────────────────────\n'
        '        # Subtle glow pulse on the curve\n'
        '        for gm in graph_mobjects:\n'
        '            self.play(\n'
        '                gm.animate.set_stroke(\n'
        '                    width=gm.get_stroke_width() + 1.5\n'
        '                ),\n'
        '                run_time=0.4,\n'
        '            )\n'
        '        self.wait(0.3)\n'
        '        for gm in graph_mobjects:\n'
        '            self.play(\n'
        '                gm.animate.set_stroke(\n'
        '                    width=gm.get_stroke_width() - 1.5\n'
        '                ),\n'
        '                run_time=0.4,\n'
        '            )\n'
        '        # Final hold\n'
        '        self.wait(3)\n'
    )

    return source


def render_scene(
    scene_path: str,
    render_config: dict,
    output_dir: str,
    timeout: int = 120,
) -> dict:
    """
    Render a Manim scene file to MP4.
    """
    import config as cfg

    quality_flag = render_config.get("manim_quality", "-qh")
    w = render_config.get("width", 1920)
    h = render_config.get("height", 1080)

    # Resolve to absolute path so cwd + relative path don't double up
    scene_path = os.path.abspath(scene_path)
    output_dir = os.path.abspath(output_dir)

    # Find the Python that has manim installed (may differ from sys.executable)
    python_exe = sys.executable
    # Check if current Python has manim; if not, look for this project's .venv
    venv_python = os.path.join(cfg.BASE_DIR, ".venv", "Scripts", "python.exe")
    if os.path.isfile(venv_python):
        python_exe = venv_python

    cmd = [
        python_exe, "-m", "manim",
        scene_path,
        "PolynomialScene",
        quality_flag,
        "--media_dir", output_dir,
    ]

    if quality_flag not in ["-ql", "-qm"]:
        cmd.extend(["-r", f"{w},{h}"])

    logger.info(f"Running manim command: {' '.join(cmd)}")

    # Clear PYTHONHOME and PYTHONPATH so dvisvgm (LaTeX SVG renderer)
    # doesn't inherit a mismatched venv path that breaks its Python.
    run_env = os.environ.copy()
    run_env.pop("PYTHONHOME", None)
    run_env.pop("PYTHONPATH", None)

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(scene_path),
            env=run_env,
        )
        duration = time.time() - start_time

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown rendering error"
            logger.error(f"Manim render failed: {error_msg}")
            return {
                "success": False,
                "video_path": None,
                "error": error_msg,
                "duration": duration,
            }

        video_path = _find_rendered_video(output_dir)
        if video_path:
            logger.info(f"Video rendered: {video_path}")
            return {
                "success": True,
                "video_path": video_path,
                "error": None,
                "duration": duration,
            }
        else:
            return {
                "success": False,
                "video_path": None,
                "error": "Render completed but output video not found.",
                "duration": duration,
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "video_path": None,
            "error": f"Rendering timed out after {timeout} seconds.",
            "duration": timeout,
        }
    except Exception as e:
        return {
            "success": False,
            "video_path": None,
            "error": str(e),
            "duration": time.time() - start_time,
        }


def _find_rendered_video(media_dir: str) -> str | None:
    """Walk the Manim media directory to find the most recently generated .mp4 file."""
    latest_time = 0
    latest_path = None

    for root, dirs, files in os.walk(media_dir):
        for f in files:
            if f.endswith(".mp4"):
                full_path = os.path.join(root, f)
                mtime = os.path.getmtime(full_path)
                if mtime > latest_time:
                    latest_time = mtime
                    latest_path = full_path

    return latest_path
