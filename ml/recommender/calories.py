"""Calorie calculation and workout duration allocation module.

Formula from the Compendium of Physical Activities:
    Burn (kcal) = MET * weight_kg * (duration_min / 60.0)
"""

from typing import Any

DEFAULT_TARGET_BURN_KCAL = 350.0
MIN_EXERCISE_DURATION_MIN = 10
MAX_EXERCISE_DURATION_MIN = 60
DEFAULT_USER_WEIGHT_KG = 70.0


def calculate_exercise_burn(
    met_value: float, weight_kg: float, duration_min: int
) -> float:
    """Calculate calories burned for a specific exercise and duration.

    Args:
        met_value: Metabolic Equivalent of Task for the exercise.
        weight_kg: User's body weight in kilograms.
        duration_min: Duration of exercise in minutes.

    Returns:
        Estimated calories burned, rounded to 1 decimal place.
    """
    if met_value <= 0 or weight_kg <= 0 or duration_min <= 0:
        return 0.0
    burn = met_value * weight_kg * (duration_min / 60.0)
    return round(burn, 1)


def allocate_exercise_durations(
    exercises: list[dict[str, Any]],
    target_kcal_burn: float = DEFAULT_TARGET_BURN_KCAL,
    weight_kg: float = DEFAULT_USER_WEIGHT_KG,
) -> list[dict[str, Any]]:
    """Allocate reasonable durations (10-60 min) to a list of recommended exercises

    so the combined session roughly matches the target calorie burn.

    Args:
        exercises: List of exercise dicts, each with at least 'met_value'.
        target_kcal_burn: Desired total session burn in kcal.
        weight_kg: User's weight in kilograms.

    Returns:
        List of exercise dicts with 'duration_min' and 'est_kcal' populated.
    """
    if not exercises:
        return []

    safe_weight = max(30.0, weight_kg)
    safe_target = max(100.0, target_kcal_burn)
    n = len(exercises)

    # Distribute the target calories equally across the N recommended exercises
    kcal_per_ex = safe_target / n
    allocated = []

    for ex in exercises:
        met = float(ex.get("met_value", 5.0))
        met = max(1.5, met)

        # duration = (target_kcal * 60) / (MET * weight)
        raw_min = (kcal_per_ex * 60.0) / (met * safe_weight)
        # Sane bounds: between 10 and 60 minutes, round to nearest 5 minutes
        bounded_min = max(
            MIN_EXERCISE_DURATION_MIN,
            min(MAX_EXERCISE_DURATION_MIN, round(raw_min / 5.0) * 5),
        )
        # Ensure at least MIN_EXERCISE_DURATION_MIN
        duration_min = max(MIN_EXERCISE_DURATION_MIN, int(bounded_min))
        est_kcal = calculate_exercise_burn(met, safe_weight, duration_min)

        ex_copy = dict(ex)
        ex_copy["duration_min"] = duration_min
        ex_copy["est_kcal"] = est_kcal
        allocated.append(ex_copy)

    return allocated
