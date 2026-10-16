"""Unit and Integration Tests for Myfitness Recommender Package.

Covers:
1. MET calorie calculation.
2. Hard vegetarian safety filter (veg users NEVER get nonveg foods).
3. Joint/injury filtering (contraindicated exercises are excluded).
4. Cold start handling (new users with 0 interactions get sensible recommendations).
5. K-Means cluster prediction output and features.
6. API interface return contract shapes.
7. CSV fallback without MongoDB.
"""

from recommender import get_exercise_recs, get_food_recs, model_version
from recommender.calories import allocate_exercise_durations, calculate_exercise_burn
from recommender.clustering import predict_cluster
from recommender.data_access import CsvDataAccess


def test_model_version_exposed():
    """Verify model_version string is exposed for Member A to store in recommendations."""
    assert isinstance(model_version, str)
    assert len(model_version) > 0


def test_met_calorie_calculation():
    """Verify MET calorie burn formula: kcal = MET * weight_kg * hours."""
    # 70 kg person jogging (MET = 7.0) for 30 minutes (0.5 hours) -> 7.0 * 70 * 0.5 = 245.0 kcal
    burn = calculate_exercise_burn(met_value=7.0, weight_kg=70.0, duration_min=30)
    assert burn == 245.0

    # 60 kg person walking (MET = 3.8) for 60 minutes -> 3.8 * 60 * 1.0 = 228.0 kcal
    burn_walk = calculate_exercise_burn(met_value=3.8, weight_kg=60.0, duration_min=60)
    assert burn_walk == 228.0

    # Zero or negative handling
    assert calculate_exercise_burn(0, 70, 30) == 0.0
    assert calculate_exercise_burn(5.0, -10, 30) == 0.0
    assert calculate_exercise_burn(5.0, 70, 0) == 0.0


def test_duration_allocation_bounds():
    """Ensure exercise duration allocation adheres to sane bounds (10-60 min)."""
    sample_exercises = [
        {"exercise_id": "ex_001", "name": "Brisk Walking", "met_value": 3.8},
        {"exercise_id": "ex_006", "name": "Jump Rope", "met_value": 10.0},
    ]
    allocated = allocate_exercise_durations(
        sample_exercises, target_kcal_burn=300.0, weight_kg=70.0
    )
    assert len(allocated) == 2
    for item in allocated:
        assert 10 <= item["duration_min"] <= 60
        assert item["est_kcal"] > 0


def test_veg_user_never_receives_nonveg():
    """HARD CONTRACT ASSERTION: A vegetarian user must NEVER be recommended non-veg foods."""
    da = CsvDataAccess()
    foods_df = da.get_foods()
    nonveg_food_ids = set(foods_df[foods_df["diet_type"] == "nonveg"]["_id"].tolist())

    # Find a veg user from dataset or create a synthetic test user
    users_df = da.get_all_users()
    veg_users = users_df[users_df["diet_type"] == "veg"]["_id"].head(5).tolist()

    for uid in veg_users:
        recs = get_food_recs(user_id=uid, kcal_target=450.0, n=4, data_access=da)
        assert len(recs) == 4
        for item in recs:
            assert (
                item["food_id"] not in nonveg_food_ids
            ), f"VIOLATION: Vegetarian user {uid} received nonveg food {item['food_id']} ({item['name']})"


def test_injury_filtering():
    """Verify that contraindicated exercises are not recommended to injured users."""
    da = CsvDataAccess()
    exercises_df = da.get_exercises()

    # User with severe knee injury
    # Running, Jumping jacks, Burpees have knee flags
    users_df = da.get_all_users()
    knee_users = (
        users_df[users_df["injuries"].astype(str).str.contains("knee")]["_id"]
        .head(5)
        .tolist()
    )

    knee_flagged_exercises = set()
    for _, row in exercises_df.iterrows():
        flags = [
            f.strip().lower() for f in str(row["injury_flags"]).split(";") if f.strip()
        ]
        if "knee" in flags:
            knee_flagged_exercises.add(str(row["_id"]))

    for uid in knee_users:
        recs = get_exercise_recs(user_id=uid, n=4, data_access=da)
        for item in recs:
            assert (
                item["exercise_id"] not in knee_flagged_exercises
            ), f"VIOLATION: Knee-injured user {uid} received contraindicated exercise {item['exercise_id']}"


def test_cold_start_new_user():
    """Verify that a brand new user with 0 interactions receives valid recommendations."""
    da = CsvDataAccess()
    unknown_user_id = "usr_non_existent_9999"

    ex_recs = get_exercise_recs(user_id=unknown_user_id, n=3, data_access=da)
    assert len(ex_recs) == 3
    for ex in ex_recs:
        assert "exercise_id" in ex
        assert "name" in ex
        assert "duration_min" in ex
        assert "est_kcal" in ex
        assert "reason" in ex

    food_recs = get_food_recs(
        user_id=unknown_user_id, kcal_target=350.0, n=3, data_access=da
    )
    assert len(food_recs) == 3
    for fd in food_recs:
        assert "food_id" in fd
        assert "name" in fd
        assert "grams" in fd
        assert "kcal" in fd
        assert "macros" in fd
        assert "reason" in fd


def test_cluster_prediction_shape():
    """Verify predict_cluster returns valid cluster_id, cluster_label, and features."""
    sample_user = {
        "_id": "usr_test",
        "profile": {
            "age": 29,
            "gender": "male",
            "height_cm": 178.0,
            "weight_kg": 82.0,
            "activity_level": "moderately_active",
            "diet_type": "veg",
            "injuries": ["knee"],
        },
        "goal": {
            "target_weight_kg": 75.0,
            "target_date": "2026-11-01",
        },
    }
    sample_logs = [
        {"sleep_hours": 7.5, "workouts": [{"duration_min": 45}]},
        {"sleep_hours": 6.8, "workouts": [{"duration_min": 30}]},
    ]

    cluster_info = predict_cluster(sample_user, sample_logs)
    assert "cluster_id" in cluster_info
    assert isinstance(cluster_info["cluster_id"], int)
    assert "cluster_label" in cluster_info
    assert isinstance(cluster_info["cluster_label"], str)
    assert "features" in cluster_info
    assert "bmi" in cluster_info["features"]
    assert "goal_delta" in cluster_info["features"]


def test_api_contract_return_shapes():
    """Strictly assert keys and types required by the shared REST API contract."""
    da = CsvDataAccess()
    users = da.get_all_users()
    test_user_id = users.iloc[0]["_id"]

    # 1. Exercises shape: [{exercise_id, name, duration_min, est_kcal, reason}]
    ex_recs = get_exercise_recs(user_id=test_user_id, n=4, data_access=da)
    assert len(ex_recs) == 4
    for item in ex_recs:
        assert set(item.keys()) == {
            "exercise_id",
            "name",
            "duration_min",
            "est_kcal",
            "reason",
        }
        assert isinstance(item["exercise_id"], str)
        assert isinstance(item["name"], str)
        assert isinstance(item["duration_min"], int)
        assert isinstance(item["est_kcal"], (float, int))
        assert isinstance(item["reason"], str)

    # 2. Foods shape: [{food_id, name, grams, kcal, macros, reason}]
    food_recs = get_food_recs(
        user_id=test_user_id, kcal_target=500.0, n=3, data_access=da
    )
    assert len(food_recs) == 3
    for item in food_recs:
        assert set(item.keys()) == {
            "food_id",
            "name",
            "diet_type",
            "grams",
            "kcal",
            "macros",
            "reason",
        }
        assert item["diet_type"] in ("veg", "nonveg")
        assert isinstance(item["food_id"], str)
        assert isinstance(item["name"], str)
        assert isinstance(item["grams"], (float, int))
        assert isinstance(item["kcal"], (float, int))
        assert isinstance(item["macros"], dict)
        assert set(item["macros"].keys()) == {
            "protein_g",
            "carbs_g",
            "fat_g",
            "fiber_g",
        }
        assert isinstance(item["reason"], str)
