from backend.app.schemas.all_schemas import (
    ExerciseRecItem,
    FoodRecItem,
)
from backend.app.services.recommender_mock import get_exercise_recs, get_food_recs


def test_mock_get_exercise_recs_count():
    recs = get_exercise_recs("user_test_123", n=2)
    assert len(recs) == 2
    assert isinstance(recs[0], ExerciseRecItem)
    assert recs[0].exercise_id is not None
    assert recs[0].duration_min > 0
    assert recs[0].est_kcal > 0
    assert len(recs[0].reason) > 0


def test_mock_get_food_recs_count():
    recs = get_food_recs("user_test_123", kcal_target=2100.0, n=3)
    assert len(recs) == 3
    assert isinstance(recs[0], FoodRecItem)
    assert recs[0].food_id is not None
    assert recs[0].macros.protein_g > 0
    assert recs[0].kcal > 0
    assert len(recs[0].reason) > 0
