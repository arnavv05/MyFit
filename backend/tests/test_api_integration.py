import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.api.deps import get_current_user
from backend.app.db.mongodb import get_database
from backend.app.core.security import create_access_token


class InMemoryAsyncDatabase:
    """Lightweight in-memory MongoDB stand-in for integration tests."""

    def __init__(self):
        self._collections: dict[str, list[dict]] = {
            "users": [],
            "daily_logs": [],
            "exercises": [
                {
                    "_id": "ex_pushups",
                    "name": "Standard Pushups",
                    "category": "Strength",
                    "muscle_group": "Chest",
                    "met_value": 3.8,
                    "difficulty": "Beginner",
                    "equipment": "Bodyweight",
                    "injury_flags": ["wrist"],
                }
            ],
            "foods": [
                {
                    "_id": "food_oatmeal",
                    "name": "Rolled Oatmeal with Water",
                    "diet_type": "veg",
                    "kcal_per_100g": 68.0,
                    "protein_g": 2.4,
                    "carbs_g": 12.0,
                    "fat_g": 1.4,
                    "fiber_g": 1.7,
                    "cuisine": "Breakfast",
                }
            ],
            "interactions": [],
            "recommendations": [],
        }

    def __getitem__(self, name: str):
        class MockCollection:
            def __init__(self, data: list[dict]):
                self.data = data

            async def find_one(self, filter_dict: dict):
                for item in self.data:
                    match = True
                    for k, v in filter_dict.items():
                        if item.get(k) != v:
                            match = False
                            break
                    if match:
                        return item
                return None

            async def insert_one(self, doc: dict):
                self.data.append(doc)
                return doc

            async def update_one(
                self, filter_dict: dict, update_dict: dict, upsert: bool = False
            ):
                existing = await self.find_one(filter_dict)
                if existing:
                    if "$set" in update_dict:
                        existing.update(update_dict["$set"])
                elif upsert:
                    new_item = {**filter_dict, **update_dict.get("$set", {})}
                    self.data.append(new_item)

            def find(self, filter_dict: dict = None):
                filter_dict = filter_dict or {}
                matched = []
                for item in self.data:
                    match = True
                    for k, v in filter_dict.items():
                        if isinstance(v, dict):
                            # Handle date range queries like $gte, $lte
                            val = item.get(k)
                            if "$gte" in v and (val is None or val < v["$gte"]):
                                match = False
                            if "$lte" in v and (val is None or val > v["$lte"]):
                                match = False
                        elif item.get(k) != v:
                            match = False
                            break
                    if match:
                        matched.append(item)

                class MockCursor:
                    def __init__(self, items):
                        self.items = items

                    def sort(self, *args, **kwargs):
                        return self

                    async def to_list(self, length: int):
                        return self.items[:length]

                return MockCursor(matched)

            async def count_documents(self, filter_dict: dict):
                return len(self.data)

            def aggregate(self, pipeline: list):
                class MockAggCursor:
                    async def to_list(self, length: int):
                        return []

                return MockAggCursor()

        return MockCollection(self._collections.setdefault(name, []))


mock_db = InMemoryAsyncDatabase()

mock_test_user = {
    "_id": "test_user_id_123",
    "email": "test@example.com",
    "password_hash": "$2b$12$eX8...",
    "profile": {
        "age": 25,
        "gender": "male",
        "height_cm": 180.0,
        "weight_kg": 75.0,
        "activity_level": "moderately_active",
        "diet_type": "veg",
        "injuries": [],
    },
    "goal": {
        "target_weight_kg": 70.0,
        "target_date": "2026-12-31",
    },
    "cluster_id": None,
    "created_at": "2026-10-12T00:00:00+00:00",
}


@pytest.fixture
def auth_headers():
    token = create_access_token(
        {"sub": mock_test_user["_id"], "email": mock_test_user["email"]}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_app():
    # Override database and auth dependencies
    app.dependency_overrides[get_database] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_test_user
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_get_users_me(test_app, auth_headers):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["profile"]["diet_type"] == "veg"


@pytest.mark.asyncio
async def test_post_and_get_daily_log(test_app, auth_headers):
    payload = {
        "date": "2026-10-12",
        "weight_kg": 74.5,
        "sleep_hours": 7.5,
        "water_ml": 2500,
        "workouts": [
            {
                "exercise_id": "ex_pushups",
                "duration_min": 20.0,
                "kcal_burned": 95.0,
                "rating": 5,
            }
        ],
        "meals": [
            {
                "food_id": "food_oatmeal",
                "grams": 200.0,
                "kcal": 136.0,
            }
        ],
    }

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        post_resp = await ac.post("/api/v1/logs", json=payload, headers=auth_headers)
        assert post_resp.status_code == 200
        post_data = post_resp.json()
        assert post_data["kcal_in"] == 136.0
        assert post_data["kcal_out"] == 95.0

        get_resp = await ac.get(
            "/api/v1/logs?from=2026-10-01&to=2026-10-31", headers=auth_headers
        )
        assert get_resp.status_code == 200
        logs = get_resp.json()
        assert len(logs) >= 1
        assert logs[0]["date"] == "2026-10-12"


@pytest.mark.asyncio
async def test_get_recommend_exercises(test_app, auth_headers):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/recommend/exercises?limit=2", headers=auth_headers)
    assert resp.status_code == 200
    recs = resp.json()
    assert len(recs) == 2
    assert "est_kcal" in recs[0]
    assert "reason" in recs[0]


@pytest.mark.asyncio
async def test_get_recommend_foods(test_app, auth_headers):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/recommend/foods?limit=2", headers=auth_headers)
    assert resp.status_code == 200
    recs = resp.json()
    assert len(recs) == 2
    assert "macros" in recs[0]
    assert "reason" in recs[0]


@pytest.mark.asyncio
async def test_post_feedback(test_app, auth_headers):
    payload = {
        "item_type": "exercise",
        "item_id": "ex_pushups",
        "rating": 5,
    }
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        resp = await ac.post("/api/v1/feedback", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["item_id"] == "ex_pushups"
    assert data["rating"] == 5
    assert data["implicit_score"] == 1.0


@pytest.mark.asyncio
async def test_get_analytics(test_app, auth_headers):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        me_resp = await ac.get("/api/v1/analytics/me", headers=auth_headers)
        assert me_resp.status_code == 200
        assert "total_workouts_completed" in me_resp.json()

        pop_resp = await ac.get("/api/v1/analytics/population")
        assert pop_resp.status_code == 200
        assert "total_users" in pop_resp.json()


@pytest.mark.asyncio
async def test_register_minimal_and_login(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        reg_payload = {
            "email": "newuser@example.com",
            "password": "securepassword123",
        }
        reg_resp = await ac.post("/api/v1/auth/register", json=reg_payload)
        assert reg_resp.status_code == 201
        data = reg_resp.json()
        assert data["email"] == "newuser@example.com"
        assert data["profile"]["activity_level"] == "moderately_active"

        # Login
        login_resp = await ac.post(
            "/api/v1/auth/login",
            json={"email": "newuser@example.com", "password": "securepassword123"},
        )
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()


@pytest.mark.asyncio
async def test_get_catalog(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert "exercises" in data
        assert "foods" in data
        assert len(data["exercises"]) >= 1


@pytest.mark.asyncio
async def test_duplicate_registration_returns_409(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        payload = {"email": "dup@example.com", "password": "password123"}
        r1 = await ac.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201

        r2 = await ac.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409


@pytest.mark.asyncio
async def test_invalid_login_returns_401(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        r = await ac.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrong"},
        )
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_and_goal(test_app, auth_headers):
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        update_payload = {
            "profile": {
                "age": 28,
                "gender": "male",
                "height_cm": 182.0,
                "weight_kg": 76.0,
                "activity_level": "very_active",
                "diet_type": "veg",
                "injuries": ["shoulder"],
            },
            "goal": {
                "target_weight_kg": 72.0,
                "target_date": "2026-11-30",
            },
        }
        resp = await ac.put(
            "/api/v1/users/me", json=update_payload, headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["profile"]["age"] == 28
        assert data["goal"]["target_weight_kg"] == 72.0


@pytest.mark.asyncio
async def test_full_auth_lifecycle(test_app):
    """Complete auth lifecycle test: register, duplicate check, wrong password check, valid login, get me."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        email = "lifecycle@example.com"
        pw = "CorrectPass123"

        # 1. Register
        r_reg = await ac.post(
            "/api/v1/auth/register", json={"email": email, "password": pw}
        )
        assert r_reg.status_code == 201
        assert r_reg.json()["email"] == email

        # 2. Duplicate registration -> 409
        r_dup = await ac.post(
            "/api/v1/auth/register", json={"email": email, "password": pw}
        )
        assert r_dup.status_code == 409

        # 3. Wrong password -> 401
        r_wrong = await ac.post(
            "/api/v1/auth/login", json={"email": email, "password": "WrongPassword!"}
        )
        assert r_wrong.status_code == 401

        # 4. Correct login -> 200 + access_token
        r_login = await ac.post(
            "/api/v1/auth/login", json={"email": email, "password": pw}
        )
        assert r_login.status_code == 200
        token = r_login.json()["access_token"]
        assert token

        # 5. Access /users/me with token -> 200 (test actual dependency without mock_test_user override)
        test_app.dependency_overrides.pop(get_current_user, None)
        try:
            r_me = await ac.get(
                "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
            )
            assert r_me.status_code == 200
            assert r_me.json()["email"] == email
        finally:
            test_app.dependency_overrides[get_current_user] = lambda: mock_test_user
