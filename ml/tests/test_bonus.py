"""Unit tests for the Bonus module (Weight Goal Forecasting & Anomaly Detection).

Tests:
1. Forecast with synthetic downward trend (returns valid future expected_date).
2. Forecast with flat trend (returns expected_date=None with clear message).
3. Forecast with fewer than 7 logs (returns expected_date=None).
4. Weight anomaly detection catches injected 5 kg spike.
5. Empty/absent logs return empty lists and None without crashing.
"""

from typing import Any

import pandas as pd
from recommender.anomaly import detect_daily_log_anomalies, detect_weight_anomalies
from recommender.data_access import BaseDataAccess
from recommender.forecast import forecast_goal_date


class MockDataAccess(BaseDataAccess):
    """Configurable in-memory DataAccess for isolated testing of edge cases."""

    def __init__(
        self,
        user: dict[str, Any] | None = None,
        logs: list[dict[str, Any]] | None = None,
    ) -> None:
        self._user = user
        self._logs = logs or []

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        return self._user

    def get_all_users(self) -> pd.DataFrame:
        return pd.DataFrame([self._user]) if self._user else pd.DataFrame()

    def get_exercises(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_foods(self) -> pd.DataFrame:
        return pd.DataFrame()

    def get_user_logs(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        return self._logs[:limit]

    def get_all_logs(self) -> pd.DataFrame:
        return pd.DataFrame(self._logs)

    def get_interactions(self, item_type: str | None = None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_user_interactions(
        self, user_id: str, item_type: str | None = None
    ) -> pd.DataFrame:
        return pd.DataFrame()


def test_forecast_downward_trend_success():
    """Verify that a steady downward trend forecasts a realistic future goal date."""
    user = {
        "_id": "usr_test_forecast",
        "profile": {"weight_kg": 80.0},
        "goal": {"target_weight_kg": 75.0, "target_date": "2026-12-31"},
    }
    # 10 days of steady 0.1 kg/day loss
    logs = [
        {"date": f"2026-09-{i:02d}", "weight_kg": 80.0 - (0.1 * i)}
        for i in range(1, 11)
    ]
    da = MockDataAccess(user=user, logs=logs)

    result = forecast_goal_date(user_id="usr_test_forecast", data_access=da)

    assert result["expected_date"] is not None
    assert result["days_remaining"] is not None
    assert result["days_remaining"] > 0
    assert result["weekly_rate_kg"] < 0
    assert "On track" in result["message"] or "Projected" in result["message"]


def test_forecast_flat_trend_returns_none():
    """Verify that a flat trend returns expected_date=None with actionable feedback."""
    user = {
        "_id": "usr_flat",
        "profile": {"weight_kg": 80.0},
        "goal": {"target_weight_kg": 72.0, "target_date": "2026-12-31"},
    }
    # 10 days of flat weight
    logs = [{"date": f"2026-09-{i:02d}", "weight_kg": 80.0} for i in range(1, 11)]
    da = MockDataAccess(user=user, logs=logs)

    result = forecast_goal_date(user_id="usr_flat", data_access=da)

    assert result["expected_date"] is None
    assert result["days_remaining"] is None
    assert result["on_track"] is False
    assert "flat" in result["message"].lower()


def test_forecast_insufficient_logs_returns_none():
    """Verify that fewer than 7 logged days returns expected_date=None."""
    user = {
        "_id": "usr_few_logs",
        "profile": {"weight_kg": 75.0},
        "goal": {"target_weight_kg": 70.0, "target_date": "2026-12-31"},
    }
    # Only 4 logged days
    logs = [
        {"date": f"2026-09-{i:02d}", "weight_kg": 75.0 - (0.1 * i)} for i in range(1, 5)
    ]
    da = MockDataAccess(user=user, logs=logs)

    result = forecast_goal_date(user_id="usr_few_logs", data_access=da)

    assert result["expected_date"] is None
    assert result["days_remaining"] is None
    assert "Insufficient data" in result["message"]


def test_anomaly_detection_catches_injected_spike():
    """Verify that a sudden 5 kg weight spike is flagged as an anomaly."""
    # 8 days baseline, then a 5 kg spike on day 9
    logs = [
        {"date": f"2026-09-{i:02d}", "weight_kg": 70.0 + (0.05 * (i % 2))}
        for i in range(1, 9)
    ]
    # Injected 5 kg spike
    logs.append({"date": "2026-09-09", "weight_kg": 75.2})

    da = MockDataAccess(logs=logs)
    anomalies = detect_weight_anomalies(user_id="usr_spike", data_access=da)

    assert len(anomalies) >= 1
    flagged_dates = [a["date"] for a in anomalies]
    assert "2026-09-09" in flagged_dates
    spike_anomaly = next(a for a in anomalies if a["date"] == "2026-09-09")
    assert (
        "shift" in spike_anomaly["reason"].lower()
        or "outlier" in spike_anomaly["reason"].lower()
    )


def test_empty_logs_handled_gracefully():
    """Verify that completely empty logs return empty list / None without raising exceptions."""
    da = MockDataAccess(user=None, logs=[])

    forecast = forecast_goal_date(user_id="usr_empty", data_access=da)
    assert forecast["expected_date"] is None
    assert forecast["days_remaining"] is None

    weight_anomalies = detect_weight_anomalies(user_id="usr_empty", data_access=da)
    assert weight_anomalies == []

    log_anomalies = detect_daily_log_anomalies(user_id="usr_empty", data_access=da)
    assert log_anomalies == []
