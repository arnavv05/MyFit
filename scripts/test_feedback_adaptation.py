import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"
client = httpx.Client(base_url=BASE_URL, timeout=30.0)

email = f"feedback_test_{uuid.uuid4().hex[:6]}@example.com"
pw = "Password123!"

client.post("/auth/register", json={"email": email, "password": pw})
token = client.post("/auth/login", json={"email": email, "password": pw}).json()[
    "access_token"
]
headers = {"Authorization": f"Bearer {token}"}
client.put(
    "/users/me",
    json={
        "profile": {
            "age": 24,
            "gender": "male",
            "height_cm": 178.0,
            "weight_kg": 75.0,
            "activity_level": "moderately_active",
            "diet_type": "nonveg",
            "injuries": [],
        },
        "goal": {"target_weight_kg": 75.0, "target_date": "2026-12-31"},
    },
    headers=headers,
)

# 1. Get initial exercise recommendations
ex_recs_1 = client.get("/recommend/exercises?limit=5", headers=headers).json()
ex_ids_1 = [x["exercise_id"] for x in ex_recs_1]
print("Initial exercise recs:", [(x["exercise_id"], x["name"]) for x in ex_recs_1])

# Rate the top item 1-star (dislike)
disliked_ex = ex_recs_1[0]["exercise_id"]
r_fb1 = client.post(
    "/feedback",
    json={"item_type": "exercise", "item_id": disliked_ex, "rating": 1},
    headers=headers,
)
assert r_fb1.status_code == 201, f"Feedback failed: {r_fb1.text}"
print(f"Rated {disliked_ex} ({ex_recs_1[0]['name']}) 1 STAR.")

# 2. Get recommendations again - disliked exercise MUST disappear!
ex_recs_2 = client.get("/recommend/exercises?limit=5", headers=headers).json()
ex_ids_2 = [x["exercise_id"] for x in ex_recs_2]
print(
    "Exercise recs after 1-star feedback:",
    [(x["exercise_id"], x["name"]) for x in ex_recs_2],
)
assert (
    disliked_ex not in ex_ids_2
), f"Disliked exercise {disliked_ex} is still present in recommendations!"
print(
    f"[PASS] Disliked item {disliked_ex} successfully disappeared from recommendations!"
)

# 3. Test Food Feedback
fd_recs_1 = client.get("/recommend/foods?limit=4", headers=headers).json()
print("\nInitial food recs:", [(f["food_id"], f["name"]) for f in fd_recs_1])
disliked_fd = fd_recs_1[0]["food_id"]
r_fb2 = client.post(
    "/feedback",
    json={"item_type": "food", "item_id": disliked_fd, "rating": 1},
    headers=headers,
)
assert r_fb2.status_code == 201
print(f"Rated food {disliked_fd} ({fd_recs_1[0]['name']}) 1 STAR.")

fd_recs_2 = client.get("/recommend/foods?limit=4", headers=headers).json()
fd_ids_2 = [f["food_id"] for f in fd_recs_2]
print(
    "Food recs after 1-star feedback:", [(f["food_id"], f["name"]) for f in fd_recs_2]
)
assert (
    disliked_fd not in fd_ids_2
), f"Disliked food {disliked_fd} is still present in recommendations!"
print(
    f"[PASS] Disliked food {disliked_fd} successfully disappeared from recommendations!"
)
print("ALL FEEDBACK ADAPTATION TESTS PASSED!")
