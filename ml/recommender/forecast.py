"""Weight Goal Forecasting Module.

Predicts target goal attainment date using Linear / Ridge regression
on historical daily weight logs.

Handles edge cases gracefully:
- < 7 logged days -> None
- Flat trend or moving away from goal -> None
- Unrealistic timelines (> 730 days / 2 years) -> None
- Compares against user target_date to evaluate on_track status
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
from sklearn.linear_model import Ridge

from recommender.data_access import BaseDataAccess, get_data_access

MIN_LOGGED_DAYS_REQUIRED = 7
MAX_REALISTIC_DAYS_CAP = 730  # 2 years


def forecast_goal_date(
    user_id: str,
    data_access: BaseDataAccess | None = None,
) -> dict[str, Any]:
    """Forecast user target weight attainment date based on historical logs.

    Args:
        user_id: Unique string identifier of the user.
        data_access: Optional custom DataAccess instance.

    Returns:
        Dictionary with keys:
            expected_date: ISO date string (YYYY-MM-DD) or None
            days_remaining: int or None
            weekly_rate_kg: float (rate of change per 7 days)
            on_track: bool
            message: str explaining status
    """
    da = data_access or get_data_access()
    user = da.get_user(user_id)

    if not user:
        return {
            "expected_date": None,
            "days_remaining": None,
            "weekly_rate_kg": 0.0,
            "on_track": False,
            "message": f"User {user_id} not found.",
        }

    profile = user.get("profile", {})
    goal = user.get("goal", {})

    current_weight = float(profile.get("weight_kg", 70.0))
    target_weight = float(goal.get("target_weight_kg", current_weight))
    target_date_str = str(goal.get("target_date", "")).strip()

    goal_delta = target_weight - current_weight
    is_weight_loss = goal_delta < 0

    # If user has already reached goal
    if abs(goal_delta) < 0.2:
        return {
            "expected_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "days_remaining": 0,
            "weekly_rate_kg": 0.0,
            "on_track": True,
            "message": "Target weight already reached! Maintain your healthy habits.",
        }

    # Fetch daily logs
    logs = da.get_user_logs(user_id, limit=90)
    if not logs or len(logs) < MIN_LOGGED_DAYS_REQUIRED:
        logged_count = len(logs) if logs else 0
        return {
            "expected_date": None,
            "days_remaining": None,
            "weekly_rate_kg": 0.0,
            "on_track": False,
            "message": (
                f"Insufficient data: {logged_count} days logged. "
                f"Log at least {MIN_LOGGED_DAYS_REQUIRED} daily entries to generate a reliable forecast."
            ),
        }

    # Prepare DataFrame
    logs_df = pd.DataFrame(logs)
    if "date" not in logs_df.columns or "weight_kg" not in logs_df.columns:
        return {
            "expected_date": None,
            "days_remaining": None,
            "weekly_rate_kg": 0.0,
            "on_track": False,
            "message": "Logs missing required date or weight_kg fields.",
        }

    logs_df["date"] = pd.to_datetime(logs_df["date"])
    logs_df["weight_kg"] = pd.to_numeric(logs_df["weight_kg"], errors="coerce")
    logs_df = logs_df.dropna(subset=["date", "weight_kg"]).sort_values("date")

    if len(logs_df) < MIN_LOGGED_DAYS_REQUIRED:
        return {
            "expected_date": None,
            "days_remaining": None,
            "weekly_rate_kg": 0.0,
            "on_track": False,
            "message": f"Log at least {MIN_LOGGED_DAYS_REQUIRED} valid days to generate a forecast.",
        }

    # Calculate days since first log
    base_date = logs_df["date"].min()
    logs_df["day_idx"] = (logs_df["date"] - base_date).dt.days

    X = logs_df[["day_idx"]].values
    y = logs_df["weight_kg"].values

    # Fit Ridge regression (regularization avoids erratic slopes on small sample noise)
    model = Ridge(alpha=1.0, random_state=42)
    model.fit(X, y)

    daily_slope = float(model.coef_[0])
    weekly_rate_kg = round(daily_slope * 7.0, 2)

    # Check direction: must be moving towards goal
    latest_day_idx = int(logs_df["day_idx"].max())
    latest_predicted_weight = float(model.predict([[latest_day_idx]])[0])
    latest_actual_date = logs_df["date"].max()

    remaining_delta = target_weight - latest_predicted_weight

    # Weight Loss scenario (target < current): daily_slope must be negative
    if is_weight_loss:
        if daily_slope >= -0.005:  # Flat or increasing
            return {
                "expected_date": None,
                "days_remaining": None,
                "weekly_rate_kg": weekly_rate_kg,
                "on_track": False,
                "message": (
                    f"Weight trend is flat or increasing (+{weekly_rate_kg} kg/week). "
                    "Adjust calorie intake or workout intensity to resume progress toward target weight."
                ),
            }
        days_needed = round(remaining_delta / daily_slope)
    else:
        # Weight Gain scenario (target > current): daily_slope must be positive
        if daily_slope <= 0.005:  # Flat or decreasing
            return {
                "expected_date": None,
                "days_remaining": None,
                "weekly_rate_kg": weekly_rate_kg,
                "on_track": False,
                "message": (
                    f"Weight trend is flat or decreasing ({weekly_rate_kg} kg/week). "
                    "Ensure adequate caloric surplus to hit your muscle gain target."
                ),
            }
        days_needed = round(remaining_delta / daily_slope)

    if days_needed <= 0:
        days_needed = 1

    # Cap unrealistic timelines
    if days_needed > MAX_REALISTIC_DAYS_CAP:
        return {
            "expected_date": None,
            "days_remaining": None,
            "weekly_rate_kg": weekly_rate_kg,
            "on_track": False,
            "message": (
                f"At current rate ({weekly_rate_kg} kg/week), target would take over 2 years. "
                "Consider setting a nearer intermediate milestone."
            ),
        }

    expected_datetime = latest_actual_date + timedelta(days=days_needed)
    expected_date_str = expected_datetime.strftime("%Y-%m-%d")

    # Assess on_track vs target_date
    on_track = True
    if target_date_str:
        try:
            target_dt = pd.to_datetime(target_date_str)
            on_track = bool(expected_datetime <= target_dt)
        except (ValueError, TypeError):
            on_track = True

    status_msg = (
        f"On track! Projected to reach target ({target_weight} kg) by {expected_date_str} "
        f"at current rate of {weekly_rate_kg} kg/week."
        if on_track
        else f"Progressing at {weekly_rate_kg} kg/week; expected date {expected_date_str} "
        f"is past your target date ({target_date_str})."
    )

    return {
        "expected_date": expected_date_str,
        "days_remaining": days_needed,
        "weekly_rate_kg": weekly_rate_kg,
        "on_track": on_track,
        "message": status_msg,
    }
