import os
from typing import Any
import requests

from dashboard.loaders import (
    load_correlations,
    load_daily_metrics,
    load_demographics,
    load_exercise_popularity,
    load_food_macros,
)

# Why: Defaulting to local backend URL with an environment override allows flexible deployment across dev and docker.
DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def get_offline_population_analytics() -> dict[str, Any]:
    """Assemble population analytics from offline aggregate files."""
    demo = load_demographics()
    daily = load_daily_metrics()
    exercises = load_exercise_popularity()
    food = load_food_macros()

    return {
        "demographics": demo,
        "daily_metrics": daily,
        "correlations": load_correlations(),
        "exercise_popularity": exercises,
        "food_macros": food,
        "source": "offline_aggregates",
    }


def get_offline_user_analytics() -> dict[str, Any]:
    """Generate default offline benchmark data for per-user analytics view."""
    daily = load_daily_metrics()
    return {
        "total_days_logged": 14,
        "total_workouts_completed": 12,
        "total_kcal_in": 28400.0,
        "total_kcal_out": 31200.0,
        "avg_sleep_hours": daily.get("sleep_hours", {}).get("mean", 7.0),
        "avg_water_ml": daily.get("water_ml", {}).get("mean", 2400.0),
        "weight_history": [
            {"date": "2026-10-01", "weight_kg": 74.5},
            {"date": "2026-10-03", "weight_kg": 74.2},
            {"date": "2026-10-06", "weight_kg": 73.9},
            {"date": "2026-10-08", "weight_kg": 73.5},
            {"date": "2026-10-10", "weight_kg": 73.2},
            {"date": "2026-10-12", "weight_kg": 73.0},
        ],
        "source": "offline_fallback",
    }


def fetch_population_analytics(
    base_url: str = DEFAULT_API_BASE,
) -> tuple[dict[str, Any], bool]:
    """Fetch population analytics from the backend API, falling back to aggregate files on error."""
    # Why: A short timeout prevents Streamlit UI from hanging when the backend server is stopped.
    try:
        resp = requests.get(f"{base_url}/analytics/population", timeout=2.0)
        if resp.status_code == 200:
            data = resp.json()
            data["source"] = "live_api"
            return data, True
    except (requests.RequestException, ValueError):
        pass

    return get_offline_population_analytics(), False


def fetch_user_analytics(
    token: str, base_url: str = DEFAULT_API_BASE
) -> tuple[dict[str, Any], bool]:
    """Fetch personal analytics for an authenticated user, falling back to sample baseline on error."""
    if token:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(
                f"{base_url}/analytics/me", headers=headers, timeout=2.0
            )
            if resp.status_code == 200:
                data = resp.json()
                data["source"] = "live_api"
                return data, True
        except (requests.RequestException, ValueError):
            pass

    return get_offline_user_analytics(), False
