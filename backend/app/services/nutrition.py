from datetime import datetime
from backend.app.schemas.all_schemas import UserProfile, UserGoal


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "lightly_active": 1.375,
    "moderate": 1.55,
    "moderately_active": 1.55,
    "active": 1.725,
    "very_active": 1.725,
    "extra_active": 1.9,
}


def calculate_bmr(profile: UserProfile) -> float:
    """Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.

    Men:   BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age(y) + 5
    Women: BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age(y) - 161
    Other: Average of both formulae.
    """
    base = 10.0 * profile.weight_kg + 6.25 * profile.height_cm - 5.0 * profile.age
    if profile.gender == "male":
        return round(base + 5.0, 2)
    elif profile.gender == "female":
        return round(base - 161.0, 2)
    else:
        # Neutral midpoint
        return round(base - 78.0, 2)


def calculate_tdee(profile: UserProfile) -> float:
    """Calculate Total Daily Energy Expenditure (TDEE).

    TDEE = BMR * activity_multiplier
    """
    bmr = calculate_bmr(profile)
    multiplier = ACTIVITY_MULTIPLIERS.get(profile.activity_level, 1.2)
    return round(bmr * multiplier, 2)


def calculate_daily_calorie_target(profile: UserProfile, goal: UserGoal) -> float:
    """Calculate daily calorie intake target based on goal weight and timeline.

    1 kg of fat ~= 7700 kcal deficit or surplus.
    Calculates deficit/surplus required per day, with safe limits.
    """
    tdee = calculate_tdee(profile)

    try:
        target_dt = datetime.strptime(goal.target_date, "%Y-%m-%d")
        today = datetime.now()
        days_remaining = (target_dt - today).days
    except ValueError:
        days_remaining = 30

    if days_remaining <= 0:
        days_remaining = 30  # Default to 30 days if past date

    weight_diff_kg = goal.target_weight_kg - profile.weight_kg
    total_kcal_diff = weight_diff_kg * 7700.0
    daily_kcal_delta = total_kcal_diff / float(days_remaining)

    # Impose safety guardrails: max deficit of -1000 kcal/day, max surplus of +1000 kcal/day
    daily_kcal_delta = max(-1000.0, min(1000.0, daily_kcal_delta))

    # Base target
    target = tdee + daily_kcal_delta

    # Absolute safe minimum: 1200 kcal for women/other, 1500 kcal for men
    min_floor = 1500.0 if profile.gender == "male" else 1200.0
    return round(max(min_floor, target), 2)


def calculate_met_calories(met: float, weight_kg: float, duration_min: float) -> float:
    """MET formula: kcal = MET * weight_kg * hours."""
    hours = duration_min / 60.0
    return round(met * weight_kg * hours, 2)
