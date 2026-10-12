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
            # Attempt to import Member B's package interface
            import ml.recommender as real_recommender  # type: ignore

            self._engine = real_recommender
            self._is_mock = False
            logger.info("Successfully loaded Member B's real ML recommender package.")
        except ImportError:
            try:
                import recommender as standalone_recommender  # type: ignore

                self._engine = standalone_recommender
                self._is_mock = False
                logger.info("Successfully loaded standalone 'recommender' package.")
            except ImportError:
                self._engine = recommender_mock
                self._is_mock = True
                logger.warning(
                    "Member B's recommender package not detected yet. Operating in fallback mock mode."
                )

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    def get_exercise_recs(self, user_id: str, n: int = 3) -> list[ExerciseRecItem]:
        return self._engine.get_exercise_recs(user_id=user_id, n=n)

    def get_food_recs(self, user_id: str, kcal_target: float, n: int = 3) -> list[FoodRecItem]:
        return self._engine.get_food_recs(user_id=user_id, kcal_target=kcal_target, n=n)


# Singleton instance for backend dependency injection
recommender_service = RecommenderService()
