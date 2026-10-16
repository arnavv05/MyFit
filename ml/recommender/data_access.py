"""Data access layer for Myfitness recommender system.

Provides a unified interface (BaseDataAccess) to fetch data from MongoDB or fallback to CSVs.
Member A can configure MongoDataAccess via connection string or env vars, while
CsvDataAccess allows seamless offline development, local EDA, and testing.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd

from recommender.config import (
    DATA_DIR,
    DEFAULT_MONGO_DB,
    MONGO_DB_NAME_ENV,
    MONGO_URI_ENV,
)

logger = logging.getLogger(__name__)


class BaseDataAccess(ABC):
    """Abstract interface defining required data queries for the ML module."""

    @abstractmethod
    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Fetch a single user profile and goal by user_id."""

    @abstractmethod
    def get_all_users(self) -> pd.DataFrame:
        """Fetch all user records as a DataFrame."""

    @abstractmethod
    def get_exercises(self) -> pd.DataFrame:
        """Fetch all exercise catalog items."""

    @abstractmethod
    def get_foods(self) -> pd.DataFrame:
        """Fetch all food catalog items."""

    @abstractmethod
    def get_user_logs(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        """Fetch recent daily logs for a given user."""

    @abstractmethod
    def get_all_logs(self) -> pd.DataFrame:
        """Fetch all daily logs as a DataFrame."""

    @abstractmethod
    def get_interactions(self, item_type: str | None = None) -> pd.DataFrame:
        """Fetch interactions, optionally filtered by 'exercise' or 'food'."""

    @abstractmethod
    def get_user_interactions(
        self, user_id: str, item_type: str | None = None
    ) -> pd.DataFrame:
        """Fetch interactions for a single user, fresh from storage."""


class CsvDataAccess(BaseDataAccess):
    """CSV-based data access for offline development, local unit tests, and CI."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.exercises_file = self.data_dir / "exercises.csv"
        self.foods_file = self.data_dir / "foods.csv"
        self.users_file = self.data_dir / "users.csv"
        self.daily_logs_file = self.data_dir / "daily_logs.csv"
        self.interactions_file = self.data_dir / "interactions.csv"

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        if not self.users_file.exists():
            return None
        df = pd.read_csv(self.users_file)
        match = df[df["_id"] == user_id]
        if match.empty:
            return None
        row = match.iloc[0].to_dict()
        return self._format_user_dict(row)

    def get_all_users(self) -> pd.DataFrame:
        if not self.users_file.exists():
            return pd.DataFrame()
        return pd.read_csv(self.users_file)

    def get_exercises(self) -> pd.DataFrame:
        if not self.exercises_file.exists():
            return pd.DataFrame()
        return pd.read_csv(self.exercises_file)

    def get_foods(self) -> pd.DataFrame:
        if not self.foods_file.exists():
            return pd.DataFrame()
        return pd.read_csv(self.foods_file)

    def get_user_logs(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        if not self.daily_logs_file.exists():
            return []
        df = pd.read_csv(self.daily_logs_file)
        user_df = (
            df[df["user_id"] == user_id]
            .sort_values("date", ascending=False)
            .head(limit)
        )
        return user_df.to_dict(orient="records")

    def get_all_logs(self) -> pd.DataFrame:
        if not self.daily_logs_file.exists():
            return pd.DataFrame()
        return pd.read_csv(self.daily_logs_file)

    def get_interactions(self, item_type: str | None = None) -> pd.DataFrame:
        if not self.interactions_file.exists():
            return pd.DataFrame()
        df = pd.read_csv(self.interactions_file)
        if item_type:
            df = df[df["item_type"] == item_type]
        return df

    def get_user_interactions(
        self, user_id: str, item_type: str | None = None
    ) -> pd.DataFrame:
        df = self.get_interactions(item_type)
        if df.empty or "user_id" not in df.columns:
            return pd.DataFrame()
        return df[df["user_id"] == user_id]

    @staticmethod
    def _format_user_dict(row: dict[str, Any]) -> dict[str, Any]:
        """Convert flat CSV row to nested structure matching MongoDB schema."""
        injuries_val = str(row.get("injuries", ""))
        injuries = [
            i.strip()
            for i in injuries_val.split(";")
            if i.strip() and i.strip() != "nan"
        ]
        return {
            "_id": str(row["_id"]),
            "email": row.get("email"),
            "profile": {
                "age": int(row["age"]),
                "gender": str(row.get("gender", "male")),
                "height_cm": float(row["height_cm"]),
                "weight_kg": float(row["weight_kg"]),
                "activity_level": str(row.get("activity_level", "sedentary")),
                "diet_type": str(row.get("diet_type", "veg")),
                "injuries": injuries,
            },
            "goal": {
                "target_weight_kg": float(
                    row.get("target_weight_kg", row["weight_kg"])
                ),
                "target_date": str(row.get("target_date", "")),
            },
            "cluster_id": int(row["cluster_id"])
            if pd.notna(row.get("cluster_id"))
            else None,
            "created_at": str(row.get("created_at", "")),
        }


class MongoDataAccess(BaseDataAccess):
    """MongoDB data access configured for production integration with Member A's backend."""

    def __init__(self, uri: str | None = None, db_name: str | None = None) -> None:
        self.uri = uri or os.getenv(MONGO_URI_ENV)
        self.db_name = db_name or os.getenv(MONGO_DB_NAME_ENV, DEFAULT_MONGO_DB)
        self._client = None
        self._db = None

        if self.uri:
            try:
                from pymongo import MongoClient

                try:
                    import certifi

                    ca_file = certifi.where()
                except Exception:
                    ca_file = None

                kwargs = {"tlsCAFile": ca_file} if ca_file else {}
                self._client = MongoClient(
                    self.uri, serverSelectionTimeoutMS=5000, **kwargs
                )
                self._db = self._client[self.db_name]
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    f"Failed to connect to MongoDB: {e}. Fallback available."
                )

    def _is_connected(self) -> bool:
        return self._db is not None

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        if not self._is_connected():
            return CsvDataAccess().get_user(user_id)
        try:
            doc = self._db.users.find_one({"_id": user_id})
            return doc
        except Exception as e:
            logger.warning(f"Error fetching user from Mongo: {e}")
            return CsvDataAccess().get_user(user_id)

    def get_all_users(self) -> pd.DataFrame:
        if not self._is_connected():
            return CsvDataAccess().get_all_users()
        try:
            cursor = self._db.users.find()
            return pd.DataFrame(list(cursor))
        except Exception as e:
            logger.warning(f"Error fetching all users from Mongo: {e}")
            return CsvDataAccess().get_all_users()

    def get_exercises(self) -> pd.DataFrame:
        if not self._is_connected():
            return CsvDataAccess().get_exercises()
        try:
            cursor = self._db.exercises.find()
            df = pd.DataFrame(list(cursor))
            return df if not df.empty else CsvDataAccess().get_exercises()
        except Exception as e:
            logger.warning(f"Error fetching exercises from Mongo: {e}")
            return CsvDataAccess().get_exercises()

    def get_foods(self) -> pd.DataFrame:
        if not self._is_connected():
            return CsvDataAccess().get_foods()
        try:
            cursor = self._db.foods.find()
            df = pd.DataFrame(list(cursor))
            return df if not df.empty else CsvDataAccess().get_foods()
        except Exception as e:
            logger.warning(f"Error fetching foods from Mongo: {e}")
            return CsvDataAccess().get_foods()

    def get_user_logs(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        if not self._is_connected():
            return CsvDataAccess().get_user_logs(user_id, limit)
        try:
            cursor = (
                self._db.daily_logs.find({"user_id": user_id})
                .sort("date", -1)
                .limit(limit)
            )
            return list(cursor)
        except Exception as e:
            logger.warning(f"Error fetching user logs from Mongo: {e}")
            return CsvDataAccess().get_user_logs(user_id, limit)

    def get_all_logs(self) -> pd.DataFrame:
        if not self._is_connected():
            return CsvDataAccess().get_all_logs()
        try:
            cursor = self._db.daily_logs.find()
            return pd.DataFrame(list(cursor))
        except Exception as e:
            logger.warning(f"Error fetching all logs from Mongo: {e}")
            return CsvDataAccess().get_all_logs()

    def get_interactions(self, item_type: str | None = None) -> pd.DataFrame:
        if not self._is_connected():
            return CsvDataAccess().get_interactions(item_type)
        try:
            query = {"item_type": item_type} if item_type else {}
            cursor = self._db.interactions.find(query)
            return pd.DataFrame(list(cursor))
        except Exception as e:
            logger.warning(f"Error reading interactions from MongoDB: {e}")
            return CsvDataAccess().get_interactions(item_type)

    def get_user_interactions(
        self, user_id: str, item_type: str | None = None
    ) -> pd.DataFrame:
        if not self._is_connected():
            return CsvDataAccess().get_user_interactions(user_id, item_type)
        try:
            query = {"user_id": user_id}
            if item_type:
                query["item_type"] = item_type
            cursor = self._db.interactions.find(query)
            return pd.DataFrame(list(cursor))
        except Exception as e:
            logger.warning(f"Error reading user interactions from MongoDB: {e}")
            return CsvDataAccess().get_user_interactions(user_id, item_type)


class InMemoryDataAccess(BaseDataAccess):
    """In-memory data access using pre-fetched user and log objects."""

    def __init__(
        self,
        user: dict[str, Any] | None = None,
        logs: list[dict[str, Any]] | None = None,
        exercises_df: pd.DataFrame | None = None,
        foods_df: pd.DataFrame | None = None,
        interactions_df: pd.DataFrame | None = None,
    ) -> None:
        self._user = user
        self._logs = logs or []
        self._exercises_df = (
            exercises_df if exercises_df is not None else pd.DataFrame()
        )
        self._foods_df = foods_df if foods_df is not None else pd.DataFrame()
        self._interactions_df = (
            interactions_df if interactions_df is not None else pd.DataFrame()
        )

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        return self._user

    def get_all_users(self) -> pd.DataFrame:
        return pd.DataFrame([self._user]) if self._user else pd.DataFrame()

    def get_exercises(self) -> pd.DataFrame:
        return self._exercises_df

    def get_foods(self) -> pd.DataFrame:
        return self._foods_df

    def get_user_logs(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        return self._logs[:limit]

    def get_all_logs(self) -> pd.DataFrame:
        return pd.DataFrame(self._logs)

    def get_interactions(self, item_type: str | None = None) -> pd.DataFrame:
        if self._interactions_df.empty or item_type is None:
            return self._interactions_df
        if "item_type" in self._interactions_df.columns:
            return self._interactions_df[
                self._interactions_df["item_type"] == item_type
            ]
        return self._interactions_df

    def get_user_interactions(
        self, user_id: str, item_type: str | None = None
    ) -> pd.DataFrame:
        return pd.DataFrame()


def get_data_access(
    uri: str | None = None, db_name: str | None = None
) -> BaseDataAccess:
    """Factory function returning MongoDataAccess if configured, else CsvDataAccess."""
    target_uri = uri or os.getenv(MONGO_URI_ENV)
    if target_uri:
        mongo_da = MongoDataAccess(uri=target_uri, db_name=db_name)
        if mongo_da._is_connected():
            return mongo_da
    return CsvDataAccess()
