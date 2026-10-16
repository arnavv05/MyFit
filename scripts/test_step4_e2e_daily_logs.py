import sys
from pathlib import Path
import uuid
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.api_client import fetch_user_analytics

BASE_URL = "http://127.0.0.1:8000/api/v1"
client = httpx.Client(base_url=BASE_URL, timeout=30.0)

email = f"e2e_user_{uuid.uuid4().hex[:6]}@example.com"
pw = "Password123!"

print("=== STEP 4: END-TO-END DAILY LOG -> PROGRESS/DASHBOARD FLOW ===")

# 1. Register & Login
r_reg = client.post(
    "/auth/register",
    json={
        "email": email,
        "password": pw,
        "profile": {
            "age": 29,
            "gender": "male",
            "height_cm": 178.0,
            "weight_kg": 80.0,
            "activity_level": "moderately_active",
            "diet_type": "veg",
            "injuries": [],
        },
        "goal": {"target_weight_kg": 75.0, "target_date": "2026-12-31"},
    },
)
assert r_reg.status_code == 201, f"Register failed: {r_reg.text}"
user_id = r_reg.json()["_id"]

r_login = client.post("/auth/login", json={"email": email, "password": pw})
assert r_login.status_code == 200
token = r_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Registered user: id={user_id}, email={email}")

# 2. Submit Daily Logs for 3 consecutive days
dates_and_payloads = [
    {
        "date": "2026-10-14",
        "weight_kg": 80.0,
        "sleep_hours": 7.0,
        "water_ml": 2200,
        "workouts": [
            {
                "exercise_id": "ex_001",
                "duration_min": 30.0,
                "kcal_burned": 250.0,
                "rating": 5,
            }
        ],
        "meals": [{"food_id": "fd_001", "grams": 150.0, "kcal": 350.0}],
    },
    {
        "date": "2026-10-15",
        "weight_kg": 79.6,
        "sleep_hours": 7.5,
        "water_ml": 2500,
        "workouts": [
            {
                "exercise_id": "ex_002",
                "duration_min": 40.0,
                "kcal_burned": 320.0,
                "rating": 4,
            }
        ],
        "meals": [{"food_id": "fd_002", "grams": 200.0, "kcal": 420.0}],
    },
    {
        "date": "2026-10-16",
        "weight_kg": 79.2,
        "sleep_hours": 8.0,
        "water_ml": 2800,
        "workouts": [
            {
                "exercise_id": "ex_003",
                "duration_min": 45.0,
                "kcal_burned": 400.0,
                "rating": 5,
            }
        ],
        "meals": [{"food_id": "fd_003", "grams": 250.0, "kcal": 550.0}],
    },
]

for p in dates_and_payloads:
    r_log = client.post("/logs", json=p, headers=headers)
    assert r_log.status_code == 200, f"Log save failed for {p['date']}: {r_log.text}"
    saved = r_log.json()
    assert saved["kcal_in"] == p["meals"][0]["kcal"]
    assert saved["kcal_out"] == p["workouts"][0]["kcal_burned"]
    print(
        f"Saved log for {p['date']}: weight={saved['weight_kg']}kg, kcal_in={saved['kcal_in']}, kcal_out={saved['kcal_out']}"
    )

# 3. Verify GET /analytics/me
r_ana = client.get("/analytics/me", headers=headers)
assert r_ana.status_code == 200, f"Analytics failed: {r_ana.text}"
ana = r_ana.json()

print("\n--- GET /analytics/me Fresh Response ---")
print(f"Total Days Logged: {ana['total_days_logged']}")
print(f"Total Workouts: {ana['total_workouts_completed']}")
print(
    f"Current Streak: {ana['current_streak_days']} days (Best: {ana['best_streak_days']})"
)
print(f"Weight History: {[(w['date'], w['weight_kg']) for w in ana['weight_history']]}")
print(
    f"Daily Calories In vs Out: {[(c['date'], c['kcal_in'], c['kcal_out'], c['net_kcal']) for c in ana['calories_in_vs_out']]}"
)
print(f"Today Summary: {ana['today_summary']}")
print(f"Goal Progress: {ana['goal_progress_pct']}%")

assert ana["total_days_logged"] == 3
assert ana["current_streak_days"] == 3
assert len(ana["weight_history"]) == 3
assert len(ana["calories_in_vs_out"]) == 3
assert ana["today_summary"] is not None
assert ana["goal_progress_pct"] > 0

# 4. Verify Streamlit Dashboard integration via fetch_user_analytics
dash_data_jwt, is_live_jwt = fetch_user_analytics(token_or_user_id=token)
assert is_live_jwt, "Dashboard API fetch using JWT token failed!"
assert dash_data_jwt["total_days_logged"] == 3
print("\n[PASS] Streamlit fetch_user_analytics via JWT token: Live and synchronized!")

dash_data_id, is_live_id = fetch_user_analytics(token_or_user_id=user_id)
assert is_live_id, "Dashboard API fetch using user_id failed!"
assert dash_data_id["total_days_logged"] == 3
print("[PASS] Streamlit fetch_user_analytics via user_id: Live and synchronized!")

print("\n=== ALL STEP 4 END-TO-END TESTS PASSED SUCCESSFULLY! ===")
