import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"
client = httpx.Client(base_url=BASE_URL, timeout=10.0)

email = f"diag_log_{uuid.uuid4().hex[:6]}@example.com"
pw = "Password123!"

# Register & Login
client.post("/auth/register", json={"email": email, "password": pw})
token = client.post("/auth/login", json={"email": email, "password": pw}).json()[
    "access_token"
]
headers = {"Authorization": f"Bearer {token}"}

# Check logs before
logs_before = client.get("/logs", headers=headers).json()
analytics_before = client.get("/analytics/me", headers=headers).json()
print("Logs before count:", len(logs_before))
print(
    "Analytics before:",
    analytics_before.get("streak"),
    analytics_before.get("weight_history"),
)

# POST a daily log
log_payload = {
    "date": "2026-10-16",
    "weight_kg": 73.5,
    "sleep_hours": 7.5,
    "water_liters": 2.5,
    "workouts": [
        {"exercise_id": "ex_pushups", "duration_min": 30, "kcal_burned": 150.0}
    ],
    "meals": [{"food_id": "food_oatmeal", "grams": 200, "kcal": 250.0}],
}

r_log = client.post("/logs", json=log_payload, headers=headers)
print("POST /logs status:", r_log.status_code)
print("POST /logs response body:", r_log.json())

# Check logs after
logs_after = client.get("/logs", headers=headers).json()
analytics_after = client.get("/analytics/me", headers=headers).json()
print("\nLogs after count:", len(logs_after))
print("Logs after items:", logs_after)
print("\nAnalytics after streak:", analytics_after.get("streak"))
print("Analytics after weight_history:", analytics_after.get("weight_history"))
print("Analytics after today_summary:", analytics_after.get("today_summary"))
print("Analytics after calories_in_vs_out:", analytics_after.get("calories_in_vs_out"))
