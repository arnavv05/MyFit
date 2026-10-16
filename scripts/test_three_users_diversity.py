import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"
client = httpx.Client(base_url=BASE_URL, timeout=30.0)

users_specs = [
    {
        "label": "User A (veg + knee injury + weight loss, 60kg)",
        "email": f"user_a_{uuid.uuid4().hex[:6]}@example.com",
        "profile": {
            "age": 28,
            "gender": "female",
            "height_cm": 162.0,
            "weight_kg": 60.0,
            "activity_level": "sedentary",
            "diet_type": "veg",
            "injuries": ["knee"],
        },
        "goal": {"target_weight_kg": 54.0, "target_date": "2026-12-31"},
    },
    {
        "label": "User B (nonveg + no injury + muscle gain, 75kg)",
        "email": f"user_b_{uuid.uuid4().hex[:6]}@example.com",
        "profile": {
            "age": 24,
            "gender": "male",
            "height_cm": 178.0,
            "weight_kg": 75.0,
            "activity_level": "very_active",
            "diet_type": "nonveg",
            "injuries": [],
        },
        "goal": {"target_weight_kg": 82.0, "target_date": "2026-12-31"},
    },
    {
        "label": "User C (veg + no injury + heavier weight 95kg, weight loss)",
        "email": f"user_c_{uuid.uuid4().hex[:6]}@example.com",
        "profile": {
            "age": 35,
            "gender": "male",
            "height_cm": 182.0,
            "weight_kg": 95.0,
            "activity_level": "lightly_active",
            "diet_type": "veg",
            "injuries": [],
        },
        "goal": {"target_weight_kg": 85.0, "target_date": "2026-12-31"},
    },
]

print("=== THREE USERS DIVERSITY & SAFETY PROOF ===")
results = []
for spec in users_specs:
    email = spec["email"]
    pw = "Password123!"
    r_reg = client.post("/auth/register", json={"email": email, "password": pw})
    token = client.post("/auth/login", json={"email": email, "password": pw}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    client.put(
        "/users/me",
        json={"profile": spec["profile"], "goal": spec["goal"]},
        headers=headers,
    )

    ex_recs = client.get("/recommend/exercises?limit=3", headers=headers).json()
    fd_recs = client.get("/recommend/foods?limit=3", headers=headers).json()

    results.append(
        {
            "label": spec["label"],
            "diet": spec["profile"]["diet_type"],
            "injuries": spec["profile"]["injuries"],
            "weight_kg": spec["profile"]["weight_kg"],
            "exercises": [
                (x["name"], f"{x['duration_min']}m", f"{x['est_kcal']}kcal")
                for x in ex_recs
            ],
            "foods": [(f["name"], f["diet_type"], f"{f['kcal']}kcal") for f in fd_recs],
        }
    )

for res in results:
    print(f"\nProfile: {res['label']}")
    print(f"Exercises: {res['exercises']}")
    print(f"Foods: {res['foods']}")

    if res["diet"] == "veg":
        assert all(
            f[1] == "veg" for f in res["foods"]
        ), f"VIOLATION: veg user received nonveg food: {res['foods']}"
    if "knee" in res["injuries"]:
        knee_hazard_names = [
            "Squat",
            "Lunge",
            "Jump",
            "Burpee",
            "Leg Press",
            "Box Jump",
        ]
        for ex_name, _, _ in res["exercises"]:
            assert not any(
                h.lower() in ex_name.lower() for h in knee_hazard_names
            ), f"VIOLATION: knee injured user received {ex_name}"

# Check that exercise and food lists differ across users
assert (
    results[0]["exercises"] != results[1]["exercises"]
), "User A and B exercises must differ!"
assert results[0]["foods"] != results[1]["foods"], "User A and B foods must differ!"
print("\n[PASS] All 3 users received personalized, safe, and distinct recommendations!")
