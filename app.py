from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__, template_folder='.')


def safe_eval(expr: str, x: float) -> float:
    """
    Safely evaluate a mathematical expression string with variable x.
    Only allows safe math operations.
    """
    allowed_names = {
        "x": x,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "exp": math.exp,
        "log": math.log,
        "log10": math.log10,
        "sqrt": math.sqrt,
        "abs": abs,
        "pi": math.pi,
        "e": math.e,
    }
    try:
        result = eval(expr, {"__builtins__": {}}, allowed_names)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


def brents_method(f, a: float, b: float, tol: float = 1e-6, max_iter: int = 100):
    """
    Brent's method for root finding.
    Returns (root, iterations_log, converged).
    """
    fa = f(a)
    fb = f(b)

    if fa * fb > 0:
        raise ValueError("f(a) and f(b) must have opposite signs.")

    # If fa is closer to zero, swap so that |f(b)| <= |f(a)|
    if abs(fa) < abs(fb):
        a, b = b, a
        fa, fb = fb, fa

    c = a
    fc = fa
    mflag = True
    s = 0.0
    d = 0.0

    iterations = []

    for i in range(1, max_iter + 1):
        # Check convergence
        if abs(b - a) < tol or fb == 0 or fs_defined(s, fb):
            pass

        # Inverse quadratic interpolation or secant
        if fa != fc and fb != fc:
            # Inverse quadratic interpolation
            s = (
                a * fb * fc / ((fa - fb) * (fa - fc))
                + b * fa * fc / ((fb - fa) * (fb - fc))
                + c * fa * fb / ((fc - fa) * (fc - fb))
            )
            method_used = "Inverse Quadratic Interpolation"
        else:
            # Secant method
            s = b - fb * (b - a) / (fb - fa)
            method_used = "Secant"

        # Conditions to fall back to bisection
        cond1 = not (3 * a + b) / 4 < s < b and not b < s < (3 * a + b) / 4
        # More precisely: s not between (3a+b)/4 and b
        tmp1 = (3 * a + b) / 4
        cond1 = not (min(tmp1, b) < s < max(tmp1, b))
        cond2 = mflag and abs(s - b) >= abs(b - c) / 2
        cond3 = (not mflag) and abs(s - b) >= abs(c - d) / 2
        cond4 = mflag and abs(b - c) < tol
        cond5 = (not mflag) and abs(c - d) < tol

        if cond1 or cond2 or cond3 or cond4 or cond5:
            s = (a + b) / 2
            mflag = True
            method_used = "Bisection"
        else:
            mflag = False

        fs = f(s)

        iteration_data = {
            "iter": i,
            "a": round(a, 8),
            "b": round(b, 8),
            "s": round(s, 8),
            "f_a": round(fa, 8),
            "f_b": round(fb, 8),
            "f_s": round(fs, 8),
            "method": method_used,
            "error": round(abs(b - a), 8),
        }
        iterations.append(iteration_data)

        d = c
        c = b
        fc = fb

        if fa * fs < 0:
            b = s
            fb = fs
        else:
            a = s
            fa = fs

        # Ensure |f(b)| <= |f(a)|
        if abs(fa) < abs(fb):
            a, b = b, a
            fa, fb = fb, fa

        if abs(fb) < tol or abs(b - a) < tol:
            iterations[-1]["converged"] = True
            return b, iterations, True

    return b, iterations, False


def fs_defined(s, fb):
    return False  # helper placeholder


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()

    expr = data.get("expr", "").strip()
    try:
        a = float(data.get("a"))
        b = float(data.get("b"))
        tol = float(data.get("tol", 1e-6))
        max_iter = int(data.get("max_iter", 100))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid numeric inputs."}), 400

    if not expr:
        return jsonify({"error": "Function expression is required."}), 400

    if tol <= 0:
        return jsonify({"error": "Tolerance must be positive."}), 400

    if max_iter < 1 or max_iter > 500:
        return jsonify({"error": "Max iterations must be between 1 and 500."}), 400

    if abs(b - a) < 1e-15:
        return jsonify({"error": "Interval [a, b] is too small."}), 400

    def f(x):
        return safe_eval(expr, x)

    try:
        fa = f(a)
        fb = f(b)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if fa * fb > 0:
        return jsonify(
            {
                "error": (
                    f"f(a) = {fa:.6f} and f(b) = {fb:.6f} have the same sign. "
                    "Brent's method requires f(a) and f(b) to have opposite signs."
                )
            }
        ), 400

    try:
        root, iterations, converged = brents_method(f, a, b, tol, max_iter)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Computation error: {e}"}), 500

    return jsonify(
        {
            "root": round(root, 10),
            "f_root": round(f(root), 10),
            "iterations": iterations,
            "total_iterations": len(iterations),
            "converged": converged,
        }
    )


if __name__ == "__main__":
    import webbrowser
    import threading
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=True)
