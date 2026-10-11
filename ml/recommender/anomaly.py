"""Anomaly Detection Module for Daily User Health Logs.

Provides robust statistical outlier detection on:
1. Weight logs (implausible day-to-day jumps, rolling median + MAD spikes).
2. General daily health logs (abnormal sleep hours, extreme hydration volumes, calorie intake anomalies).

Designed to catch scale errors, logging typos, and physical irregularities.
"""

from typing import Any

import numpy as np
import pandas as pd

from recommender.data_access import BaseDataAccess, get_data_access

MAX_SINGLE_DAY_WEIGHT_JUMP_KG = 2.0
MAD_OUTLIER_THRESHOLD = 3.0


def detect_weight_anomalies(
    user_id: str,
    data_access: BaseDataAccess | None = None,
) -> list[dict[str, Any]]:
    """Detect anomalous weight entries for a user based on physics and robust statistics.

    Args:
        user_id: Unique string identifier of the user.
        data_access: Optional custom DataAccess instance.

    Returns:
        List of dictionaries: [{"date": str, "weight_kg": float, "reason": str}]
    """
    da = data_access or get_data_access()
    logs = da.get_user_logs(user_id, limit=90)

    if not logs or len(logs) == 0:
        return []

    df = pd.DataFrame(logs)
    if "date" not in df.columns or "weight_kg" not in df.columns:
        return []

    df["date"] = pd.to_datetime(df["date"])
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")
    df = (
        df.dropna(subset=["date", "weight_kg"])
        .sort_values("date")
        .reset_index(drop=True)
    )

    if len(df) == 0:
        return []

    anomalies: list[dict[str, Any]] = []
    seen_dates: set[str] = set()

    # 1. Physical Sanity Bounds Check (< 35 kg or > 250 kg)
    for _, row in df.iterrows():
        w = float(row["weight_kg"])
        date_str = row["date"].strftime("%Y-%m-%d")
        if w < 35.0 or w > 250.0:
            anomalies.append(
                {
                    "date": date_str,
                    "weight_kg": w,
                    "reason": f"Weight reading ({w} kg) falls outside physiological bounds (35-250 kg).",
                }
            )
            seen_dates.add(date_str)

    # 2. Day-to-Day Jump Check (> 2.0 kg within 24-48 hours)
    df["day_diff"] = (df["date"] - df["date"].shift(1)).dt.days
    df["weight_jump"] = (df["weight_kg"] - df["weight_kg"].shift(1)).abs()

    for idx in range(1, len(df)):
        row = df.iloc[idx]
        date_str = row["date"].strftime("%Y-%m-%d")
        if date_str in seen_dates:
            continue

        day_diff = row["day_diff"]
        jump = row["weight_jump"]

        # Jump check only applies if logs are within 2 days of each other
        if day_diff <= 2 and jump > MAX_SINGLE_DAY_WEIGHT_JUMP_KG:
            prev_w = float(df.iloc[idx - 1]["weight_kg"])
            curr_w = float(row["weight_kg"])
            anomalies.append(
                {
                    "date": date_str,
                    "weight_kg": curr_w,
                    "reason": (
                        f"Implausible day-to-day shift of {jump:.1f} kg "
                        f"({prev_w:.1f} kg to {curr_w:.1f} kg in {day_diff} day(s))."
                    ),
                }
            )
            seen_dates.add(date_str)

    # 3. Robust Rolling Median + MAD Outlier Detection (if at least 7 entries)
    if len(df) >= 7:
        weights = df["weight_kg"].values
        median_w = np.median(weights)
        mad = np.median(np.abs(weights - median_w))

        if mad > 0:
            modified_z_scores = 0.6745 * np.abs(weights - median_w) / mad
            for i, score in enumerate(modified_z_scores):
                date_str = df.iloc[i]["date"].strftime("%Y-%m-%d")
                if date_str not in seen_dates and score > MAD_OUTLIER_THRESHOLD:
                    w = float(df.iloc[i]["weight_kg"])
                    anomalies.append(
                        {
                            "date": date_str,
                            "weight_kg": w,
                            "reason": f"Statistical outlier ({score:.1f}x MAD deviation from user median).",
                        }
                    )
                    seen_dates.add(date_str)

    return sorted(anomalies, key=lambda x: x["date"])


def detect_daily_log_anomalies(
    user_id: str,
    data_access: BaseDataAccess | None = None,
) -> list[dict[str, Any]]:
    """Detect anomalies in sleep, hydration, or caloric logging."""
    da = data_access or get_data_access()
    logs = da.get_user_logs(user_id, limit=90)

    if not logs:
        return []

    anomalies: list[dict[str, Any]] = []
    for log in logs:
        date_str = str(log.get("date", "Unknown"))
        sleep = (
            float(log.get("sleep_hours", 7.0))
            if log.get("sleep_hours") is not None
            else 7.0
        )
        water = (
            float(log.get("water_ml", 2000.0))
            if log.get("water_ml") is not None
            else 2000.0
        )

        if sleep < 3.0 or sleep > 14.0:
            anomalies.append(
                {
                    "date": date_str,
                    "metric": "sleep_hours",
                    "value": sleep,
                    "reason": f"Sleep duration of {sleep} hours is unusually extreme (<3h or >14h).",
                }
            )

        if water < 400.0 or water > 6500.0:
            anomalies.append(
                {
                    "date": date_str,
                    "metric": "water_ml",
                    "value": water,
                    "reason": f"Water intake of {water} ml is unusually extreme (<400ml or >6500ml).",
                }
            )

    return anomalies
