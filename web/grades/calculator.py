def calculate_required_grades(numeric_grades: list[float], desired_avg: float, remaining_works: int) -> dict:
    S = sum(numeric_grades)
    N = len(numeric_grades)
    D = desired_avg
    R = remaining_works

    if R <= 0:
        current = round(S / N, 2) if N > 0 else None
        return {
            "achievable": current is not None and current >= D,
            "required_avg": None,
            "current_avg": current,
            "remaining_works": 0,
            "message": "No remaining works." if R == 0 else "Invalid number of works.",
        }

    required = (D * (N + R) - S) / R

    if required > 10:
        achievable = False
        message = f"Not achievable: would need an average of {required:.2f}, but the maximum is 10."
    elif required < 1:
        achievable = True
        required = None
        message = "Already achieved — even with minimum grades the goal will be met."
    else:
        achievable = True
        message = f"You need an average of {required:.2f} across each of the {R} remaining works."

    current_avg = round(S / N, 2) if N > 0 else None

    return {
        "achievable": achievable,
        "required_avg": round(required, 2) if required is not None else None,
        "current_avg": current_avg,
        "remaining_works": R,
        "desired_avg": D,
        "message": message,
    }


def generate_scenario_table(numeric_grades: list[float], desired_avg: float, max_works: int = 20) -> list[dict]:
    rows = []
    for r in range(1, max_works + 1):
        result = calculate_required_grades(numeric_grades, desired_avg, r)
        rows.append({
            "remaining_works": r,
            "required_avg": result["required_avg"],
            "achievable": result["achievable"],
        })
    return rows


def grade_distribution(numeric_grades: list[float]) -> dict:
    counts = {str(i): 0 for i in range(1, 11)}
    for g in numeric_grades:
        key = str(int(round(g)))
        if key in counts:
            counts[key] += 1
    return counts
