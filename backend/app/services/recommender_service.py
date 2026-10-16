"""Recommender integration: loads real ML package or falls back to mock.

Exposes:
    recommender_service.get_exercise_recs(user_id, n, target_burn_kcal)
    recommender_service.get_food_recs(user_id, kcal_target, n)
    recommender_service.is_mock  -> bool
    recommender_service.model_version  -> str
"""

import logging
import sys
from pathlib import Path
from typing import Protocol

from backend.app.schemas.all_schemas import ExerciseRecItem, FoodRecItem
from backend.app.services import recommender_mock

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Protocol (structural typing – no inheritance needed)
# ---------------------------------------------------------------------------


class RecommenderInterface(Protocol):
    """Contract expected from ml/recommender package."""

    def get_exercise_recs(
        self, user_id: str, n: int = 3, target_burn_kcal: float = 350.0
    ) -> list[ExerciseRecItem]: ...

    def get_food_recs(
        self, user_id: str, kcal_target: float, n: int = 3
    ) -> list[FoodRecItem]: ...


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class RecommenderService:
    """Facade that loads the real ML recommender or falls back to mock.

    Design decisions:
    - Tries `pip install -e ml/` path first (installed package).
    - Falls back to injecting ml/ on sys.path (dev mode).
    - If both fail, uses the deterministic mock (never raises).
    - Emits a clear WARNING log when running in mock mode so Member A
      can see it in structured logs.
    """

    def __init__(self):
        self._engine = None
        self._is_mock = True
        self._model_version = "mock-0.0.0"
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        # Attempt 1: installed package
        try:
            import recommender as _rec  # type: ignore

            self._engine = _rec
            self._is_mock = False
            self._model_version = getattr(_rec, "model_version", "unknown")
            logger.info(
                "Loaded real ML recommender package (version=%s).", self._model_version
            )
            return
        except ImportError:
            pass

        # Attempt 2: editable dev path ml/
        ml_path = str(Path(__file__).resolve().parents[3] / "ml")
        if ml_path not in sys.path:
            sys.path.insert(0, ml_path)
        try:
            import recommender as _rec  # type: ignore

            self._engine = _rec
            self._is_mock = False
            self._model_version = getattr(_rec, "model_version", "unknown")
            logger.info(
                "Loaded real ML recommender via sys.path dev mode (version=%s).",
                self._model_version,
            )
            return
        except Exception as exc:
            logger.warning(
                "Real ML recommender unavailable (%s). "
                "Running in MOCK mode – recommendations are deterministic placeholders. "
                "Run `pip install -e ml/` and ensure ml/models/ artifacts exist to enable the real engine.",
                exc,
            )

        # Fallback: deterministic mock
        self._engine = recommender_mock
        self._is_mock = True
        self._model_version = "mock-0.0.0"

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    @property
    def model_version(self) -> str:
        return self._model_version

    def get_exercise_recs(
        self,
        user_id: str,
        n: int = 3,
        target_burn_kcal: float = 350.0,
        user_dict: dict | None = None,
        date: str | None = None,
    ) -> list[ExerciseRecItem]:
        """Get exercise recommendations.

        Passes user context and date to the real package for personalized cold-start and variety.
        """
        if self._is_mock:
            raw = self._engine.get_exercise_recs(user_id=user_id, n=n)
        else:
            try:
                raw = self._engine.get_exercise_recs(
                    user_id=user_id,
                    n=n,
                    target_burn_kcal=target_burn_kcal,
                    user_dict=user_dict,
                    date=date,
                )
            except TypeError:
                try:
                    raw = self._engine.get_exercise_recs(
                        user_id=user_id, n=n, target_burn_kcal=target_burn_kcal
                    )
                except TypeError:
                    raw = self._engine.get_exercise_recs(user_id=user_id, n=n)
        return [
            item if isinstance(item, ExerciseRecItem) else ExerciseRecItem(**item)
            for item in raw
        ]

    def get_food_recs(
        self,
        user_id: str,
        kcal_target: float,
        n: int = 3,
        user_dict: dict | None = None,
        date: str | None = None,
    ) -> list[FoodRecItem]:
        """Get food recommendations calibrated to `kcal_target`."""
        if self._is_mock:
            raw = self._engine.get_food_recs(
                user_id=user_id, kcal_target=kcal_target, n=n
            )
        else:
            try:
                raw = self._engine.get_food_recs(
                    user_id=user_id,
                    kcal_target=kcal_target,
                    n=n,
                    user_dict=user_dict,
                    date=date,
                )
            except TypeError:
                raw = self._engine.get_food_recs(
                    user_id=user_id, kcal_target=kcal_target, n=n
                )
        return [
            item if isinstance(item, FoodRecItem) else FoodRecItem(**item)
            for item in raw
        ]


# Singleton – constructed once at import time, logs its mode clearly
recommender_service = RecommenderService()
