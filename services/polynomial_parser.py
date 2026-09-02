"""
Polynomial Studio — Safe Polynomial Parser

Parses user-entered polynomial strings into SymPy expressions safely.
Handles y=f(x), x=g(y), and implicit equations.
No eval/exec on raw user input.
"""
import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
    function_exponentiation,
)

TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
    function_exponentiation,
)

x = sp.Symbol("x")
y = sp.Symbol("y")


def _preprocess_input(equation_str: str) -> str:
    """
    Clean and preprocess the user's equation string.
    Returns the raw cleaned string (may contain '=' for equations).
    """
    s = equation_str.strip()

    # Normalize common notations
    s = s.replace("\u00b2", "**2").replace("\u00b3", "**3").replace("\u2074", "**4")
    s = s.replace("^", "**")

    # Convert fraction notation like (1/2)x to (1/2)*x
    s = re.sub(r"\)(\s*x)", r")*\1", s)

    s = s.strip()
    if not s:
        raise ValueError("Empty polynomial expression.")

    return s


def _try_parse_as_f_of_x(cleaned: str):
    """
    Try to parse the cleaned string as a plain expression in x.
    Returns (expr, is_polynomial) or None.
    """
    # Strip known LHS prefixes: y =, f(x) =
    stripped = re.sub(
        r"^(y|f\s*\(\s*x\s*\))\s*=\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    if "=" in stripped:
        return None  # still has an =, not a plain expression

    try:
        expr = parse_expr(
            stripped,
            local_dict={"x": x, "y": y},
            transformations=TRANSFORMATIONS,
            evaluate=True,
        )
        is_poly = expr.is_polynomial(x)
        return (expr, is_poly)
    except Exception:
        return None


def _try_solve_equation(cleaned: str):
    """
    Try to parse as an implicit equation and solve for y.
    Returns (expr, is_polynomial, is_implicit, implicit_expr) or None.
    For explicit solutions: (solved_expr, is_poly, False, None)
    For implicit fallback: (None, False, True, F(x,y))
    """
    if "=" not in cleaned:
        return None

    parts = cleaned.split("=", 1)
    lhs_str = parts[0].strip()
    rhs_str = parts[1].strip()

    try:
        lhs_expr = parse_expr(
            lhs_str,
            local_dict={"x": x, "y": y},
            transformations=TRANSFORMATIONS,
            evaluate=True,
        )
        rhs_expr = parse_expr(
            rhs_str,
            local_dict={"x": x, "y": y},
            transformations=TRANSFORMATIONS,
            evaluate=True,
        )
    except Exception:
        return None

    # Build the implicit form F(x,y) = lhs - rhs
    implicit_expr = sp.expand(lhs_expr - rhs_expr)

    try:
        solutions = sp.solve(sp.Eq(lhs_expr, rhs_expr), y)
    except Exception:
        # Can't solve symbolically — treat as implicit
        return (None, False, True, implicit_expr)

    if not solutions:
        # No solutions found — treat as implicit
        return (None, False, True, implicit_expr)

    # Prefer a solution that depends on x and is a polynomial
    for sol in solutions:
        if x in sol.free_symbols and sol.is_polynomial(x):
            return (sol, True, False, None)

    # Then any solution that depends on x (non-polynomial like sqrt(x))
    for sol in solutions:
        if x in sol.free_symbols:
            return (sol, False, False, None)

    # Constant solutions
    for sol in solutions:
        return (sol, True, False, None)

    # Fallback to implicit
    return (None, False, True, implicit_expr)


def parse_polynomial(equation_str: str) -> dict:
    """
    Parse a polynomial equation string into a validated result.

    Returns:
        {
            "success": True/False,
            "expression": sympy expression (or None),
            "latex": str,
            "polynomial_str": str,
            "degree": int or None,
            "coefficients": list or None,
            "is_polynomial": bool,
            "error": str or None
        }
    """
    default_fail = {
        "success": False,
        "expression": None,
        "latex": "",
        "polynomial_str": "",
        "degree": None,
        "coefficients": None,
        "is_polynomial": False,
        "is_implicit": False,
        "implicit_expr": None,
        "error": "",
    }

    try:
        cleaned = _preprocess_input(equation_str)
    except ValueError as e:
        return {**default_fail, "error": str(e)}

    # Strategy 1: try as y = f(x) or plain expression
    result = _try_parse_as_f_of_x(cleaned)

    # Strategy 2: try as implicit equation, solve for y
    if result is None:
        result = _try_solve_equation(cleaned)

    if result is None:
        return {
            **default_fail,
            "error": (
                f"Cannot understand: {equation_str}\n"
                "Try: y = x^2, x = y^2, or x^2 + y^2 = 25"
            ),
        }

    # Unpack result — may be (expr, is_poly) or (None, False, True, implicit_expr)
    if len(result) == 4:
        expr, is_poly, is_implicit, implicit_expr = result
    else:
        expr, is_poly = result
        is_implicit = False
        implicit_expr = None

    # Build output
    if is_implicit and implicit_expr is not None:
        latex_display = f"{sp.latex(implicit_expr)} = 0"
        polynomial_str = str(implicit_expr)
        degree = None
        coefficients = None
        try:
            poly_expr = sp.Poly(implicit_expr, x, y)
            degree = int(poly_expr.total_degree())
        except Exception:
            pass
    else:
        latex_display = f"y = {sp.latex(expr)}"
        polynomial_str = str(expr)

        degree = None
        coefficients = None
        if is_poly:
            try:
                degree = int(sp.degree(expr, x))
                if degree > 12:
                    return {
                        **default_fail,
                        "error": f"Degree {degree} is too high. Maximum supported is 12.",
                    }
                poly = sp.Poly(expr, x)
                coefficients = [float(c) for c in poly.all_coeffs()]
            except Exception:
                degree = None
                coefficients = None

    return {
        "success": True,
        "expression": expr,
        "latex": latex_display,
        "polynomial_str": polynomial_str,
        "degree": degree,
        "coefficients": coefficients,
        "is_polynomial": is_poly,
        "is_implicit": is_implicit,
        "implicit_expr": implicit_expr,
        "error": None,
    }


def to_numerical_function(expr):
    """
    Convert a SymPy expression to a safe numerical function using lambdify.
    """
    return sp.lambdify(x, expr, modules=["numpy"])
