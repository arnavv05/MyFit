import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"
client = httpx.Client(base_url=BASE_URL, timeout=10.0)


def create_user(email_prefix, profile, goal):
    email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com"
    pw = "Password123!"
    r_reg = client.post("/auth/register", json={"email": email, "password": pw})
    assert r_reg.status_code == 201, f"Reg failed: {r_reg.text}"
    user = r_reg.json()
    r_login = client.post("/auth/login", json={"email": email, "password": pw})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r_prof = client.put(
        "/users/me", json={"profile": profile, "goal": goal}, headers=headers
    )
    assert r_prof.status_code == 200, f"Profile update failed: {r_prof.text}"
    return user["_id"], email, headers


# User 1: Veg + Knee Injury, weight 60kg
u1_id, u1_email, u1_headers = create_user(
    "veg_knee",
    {
        "age": 22,
        "gender": "female",
        "height_cm": 160.0,
        "weight_kg": 60.0,
        "activity_level": "sedentary",
        "diet_type": "veg",
        "injuries": ["knee"],
    },
    {"target_weight_kg": 55.0, "target_date": "2026-12-31"},
)

# User 2: Nonveg + No Injury, weight 85kg
u2_id, u2_email, u2_headers = create_user(
    "nonveg_healthy",
    {
        "age": 25,
        "gender": "male",
        "height_cm": 185.0,
        "weight_kg": 85.0,
        "activity_level": "very_active",
        "diet_type": "nonveg",
        "injuries": [],
    },
    {"target_weight_kg": 90.0, "target_date": "2026-12-31"},
)

print(f"User 1 (Veg, Knee, 60kg): {u1_id} ({u1_email})")
print(f"User 2 (Nonveg, None, 85kg): {u2_id} ({u2_email})")

# Exercise recs
ex1 = client.get("/recommend/exercises", headers=u1_headers).json()
ex2 = client.get("/recommend/exercises", headers=u2_headers).json()

print("\n--- Exercise Recs User 1 ---")
for x in ex1:
    print(
        f"  {x.get('exercise_id')}: {x.get('name')} | duration={x.get('duration_min')} | est_kcal={x.get('est_kcal')} | reason={x.get('reason')}"
    )

print("\n--- Exercise Recs User 2 ---")
for x in ex2:
    print(
        f"  {x.get('exercise_id')}: {x.get('name')} | duration={x.get('duration_min')} | est_kcal={x.get('est_kcal')} | reason={x.get('reason')}"
    )

# Food recs
fd1 = client.get("/recommend/foods", headers=u1_headers).json()
fd2 = client.get("/recommend/foods", headers=u2_headers).json()

print("\n--- Food Recs User 1 ---")
for f in fd1:
    print(
        f"  {f.get('food_id')}: {f.get('name')} | grams={f.get('grams')} | kcal={f.get('kcal')} | diet_type={f.get('diet_type')} | reason={f.get('reason')}"
    )

print("\n--- Food Recs User 2 ---")
for f in fd2:
    print(
        f"  {f.get('food_id')}: {f.get('name')} | grams={f.get('grams')} | kcal={f.get('kcal')} | diet_type={f.get('diet_type')} | reason={f.get('reason')}"
    )

print("\nExercise recs identical?", ex1 == ex2)
print("Food recs identical?", fd1 == fd2)
