"""
Polynomial Studio — Mathematical Analyzer

Uses SymPy to analyze polynomials: roots, derivatives, extrema, end behavior, etc.
"""
import sympy as sp
import numpy as np

x = sp.Symbol("x")
y = sp.Symbol("y")


def analyze_polynomial(expr) -> dict:
    """
    Perform comprehensive mathematical analysis on a SymPy polynomial expression.

    Returns a dict with all analysis results, ready for JSON serialization.
    """
    result = {
        "degree": None,
        "leading_coefficient": None,
        "roots_real": [],
        "roots_complex": [],
        "x_intercepts": [],
        "y_intercept": None,
        "derivative": None,
        "derivative_latex": "",
        "critical_points": [],
        "local_maxima": [],
        "local_minima": [],
        "end_behavior": {},
        "expanded_form": "",
        "factorized_form": "",
        "increasing_intervals": [],
        "decreasing_intervals": [],
    }

    try:
        # Degree
        result["degree"] = int(sp.degree(expr, x))

        # Leading coefficient
        poly = sp.Poly(expr, x)
        coeffs = poly.all_coeffs()
        result["leading_coefficient"] = float(coeffs[0])

        # Expanded form
        result["expanded_form"] = str(sp.expand(expr))

        # Factorized form
        try:
            factored = sp.factor(expr)
            result["factorized_form"] = str(factored)
        except Exception:
            result["factorized_form"] = result["expanded_form"]

        # Y-intercept: f(0)
        y_int = expr.subs(x, 0)
        result["y_intercept"] = {"x": 0, "y": float(y_int)}

        # Real roots
        try:
            real_roots = sp.real_roots(expr, x)
            for r in real_roots:
                val = float(r)
                result["roots_real"].append(round(val, 6))
                result["x_intercepts"].append({"x": round(val, 6), "y": 0})
        except Exception:
            pass

        # Complex roots (only if there are non-real ones)
        try:
            all_roots = sp.solve(expr, x)
            for r in all_roots:
                if not r.is_real:
                    result["roots_complex"].append(str(r))
        except Exception:
            pass

        # Derivative
        try:
            deriv = sp.diff(expr, x)
            result["derivative"] = str(deriv)
            result["derivative_latex"] = f"f'(x) = {sp.latex(deriv)}"
        except Exception:
            pass

        # Critical points: f'(x) = 0
        try:
            deriv = sp.diff(expr, x)
            crit_solutions = sp.solve(deriv, x)
            second_deriv = sp.diff(deriv, x)

            for cp in crit_solutions:
                if cp.is_real:
                    cp_val = float(cp)
                    f_val = float(expr.subs(x, cp))
                    d2 = float(second_deriv.subs(x, cp))

                    point = {"x": round(cp_val, 6), "y": round(f_val, 6)}

                    if d2 < 0:
                        result["local_maxima"].append(point)
                    elif d2 > 0:
                        result["local_minima"].append(point)

                    result["critical_points"].append(point)
        except Exception:
            pass

        # End behavior
        degree = result["degree"]
        lc = result["leading_coefficient"]

        if degree % 2 == 0:
            if lc > 0:
                result["end_behavior"] = {
                    "x_pos_inf": "+∞",
                    "x_neg_inf": "+∞",
                    "description": "Both ends go to +∞ (even degree, positive leading coefficient)",
                }
            else:
                result["end_behavior"] = {
                    "x_pos_inf": "-∞",
                    "x_neg_inf": "-∞",
                    "description": "Both ends go to -∞ (even degree, negative leading coefficient)",
                }
        else:
            if lc > 0:
                result["end_behavior"] = {
                    "x_pos_inf": "+∞",
                    "x_neg_inf": "-∞",
                    "description": "Right end → +∞, Left end → -∞ (odd degree, positive leading coefficient)",
                }
            else:
                result["end_behavior"] = {
                    "x_pos_inf": "-∞",
                    "x_neg_inf": "+∞",
                    "description": "Right end → -∞, Left end → +∞ (odd degree, negative leading coefficient)",
                }

        # Increasing/Decreasing intervals (approximate with sign chart of derivative)
        try:
            deriv = sp.diff(expr, x)
            crit_pts = [float(cp) for cp in sp.solve(deriv, x) if cp.is_real]
            crit_pts.sort()

            test_points = []
            if crit_pts:
                # Before first critical point
                test_points.append(crit_pts[0] - 1)
                # Between critical points
                for i in range(len(crit_pts) - 1):
                    test_points.append((crit_pts[i] + crit_pts[i + 1]) / 2)
                # After last critical point
                test_points.append(crit_pts[-1] + 1)
            else:
                test_points = [0]

            increasing = False
            for tp in test_points:
                d_val = float(deriv.subs(x, tp))
                if d_val > 0:
                    increasing = True
                else:
                    increasing = False

            if increasing:
                result["increasing_intervals"] = ["increasing overall"] if not crit_pts else []
            else:
                result["decreasing_intervals"] = ["decreasing overall"] if not crit_pts else []

        except Exception:
            pass

    except Exception as e:
        result["error"] = str(e)

    return result


def compute_graph_data(expr, x_min: float, x_max: float, num_points: int = 500) -> dict:
    """
    Compute numerical data points for graphing a polynomial.
    """
    try:
        f = sp.lambdify(x, expr, modules=["numpy"])
        x_vals = np.linspace(x_min, x_max, num_points)
        y_vals = f(x_vals)

        # Handle any NaN/Inf values
        y_vals = np.where(np.isfinite(y_vals), y_vals, np.nan)

        # Auto-compute y range
        valid_y = y_vals[np.isfinite(y_vals)]
        if len(valid_y) > 0:
            y_min_auto = float(np.nanmin(valid_y))
            y_max_auto = float(np.nanmax(valid_y))
            # Add padding
            y_range = y_max_auto - y_min_auto
            if y_range == 0:
                y_range = 2
            y_min_auto -= y_range * 0.15
            y_max_auto += y_range * 0.15
        else:
            y_min_auto, y_max_auto = -5, 5

        return {
            "x": x_vals.tolist(),
            "y": y_vals.tolist(),
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min_auto,
            "y_max": y_max_auto,
        }
    except Exception as e:
        return {"error": str(e), "x": [], "y": [], "x_min": x_min, "x_max": x_max, "y_min": -5, "y_max": 5}


def compute_graph_data_implicit(implicit_expr, x_min: float, x_max: float,
                                 y_min: float = -2, y_max: float = 2,
                                 num_points: int = 400) -> dict:
    """
    Compute contour data for an implicit equation F(x, y) = 0.
    Uses matplotlib's marching squares contour tracer.
    Returns a list of contour segments as (x[], y[]) pairs.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        # Create a grid
        x_arr = np.linspace(x_min, x_max, num_points)
        y_arr = np.linspace(y_min, y_max, num_points)
        X, Y = np.meshgrid(x_arr, y_arr)

        # Evaluate F(x, y) on the grid
        f = sp.lambdify((x, y), implicit_expr, modules=["numpy"])
        Z = f(X, Y)

        # Replace non-finite values with NaN
        Z = np.where(np.isfinite(Z), Z, np.nan)

        # Use matplotlib to trace the zero-level contour
        fig, ax = plt.subplots()
        cs = ax.contour(X, Y, Z, levels=[0])
        plt.close(fig)

        # Extract contour segments (works with matplotlib 3.8+)
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

        return {
            "segments_x": segments_x,
            "segments_y": segments_y,
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max,
        }
    except Exception as e:
        return {
            "error": str(e),
            "segments_x": [],
            "segments_y": [],
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max,
        }
