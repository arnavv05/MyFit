import logging
from typing import Protocol
from backend.app.schemas.all_schemas import ExerciseRecItem, FoodRecItem
from backend.app.services import recommender_mock

logger = logging.getLogger(__name__)


class RecommenderInterface(Protocol):
    """Protocol defining the exact contract expected from Member B's recommender package."""

    def get_exercise_recs(self, user_id: str, n: int = 3) -> list[ExerciseRecItem]: ...

    def get_food_recs(self, user_id: str, kcal_target: float, n: int = 3) -> list[FoodRecItem]: ...


class RecommenderService:
    """Facade for the recommender engine.

    Gracefully detects and loads Member B's ML recommender module (`ml.recommender` or `recommender`).
    If not available, seamlessly falls back to the deterministic recommender_mock so that
    endpoints and Member C's frontend never experience interruptions.
    """

    def __init__(self):
        self._engine = None
        self._is_mock = True
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        try:
            import recommender as real_recommender  # type: ignore

            self._engine = real_recommender
            self._is_mock = False
            logger.info("Successfully loaded Member B's real ML recommender package.")
        except ImportError:
            try:
                import sys
                from pathlib import Path

                ml_path = str(Path(__file__).resolve().parents[3] / "ml")
                if ml_path not in sys.path:
                    sys.path.insert(0, ml_path)

                import recommender as real_recommender  # type: ignore

                self._engine = real_recommender
                self._is_mock = False
                logger.info("Successfully loaded Member B's real ML recommender package via ml path.")
            except Exception as e:
                self._engine = recommender_mock
                self._is_mock = True
                logger.warning(
                    f"Member B's recommender package not active ({e}). Operating in fallback mock mode."
                )

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    def get_exercise_recs(self, user_id: str, n: int = 3) -> list[ExerciseRecItem]:
        raw = self._engine.get_exercise_recs(user_id=user_id, n=n)
        return [item if isinstance(item, ExerciseRecItem) else ExerciseRecItem(**item) for item in raw]

    def get_food_recs(self, user_id: str, kcal_target: float, n: int = 3) -> list[FoodRecItem]:
        raw = self._engine.get_food_recs(user_id=user_id, kcal_target=kcal_target, n=n)
        return [item if isinstance(item, FoodRecItem) else FoodRecItem(**item) for item in raw]


# Singleton instance for backend dependency injection
recommender_service = RecommenderService()
