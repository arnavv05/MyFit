"""K-Means user clustering module.

Clusters users into meaningful fitness personas based on:
- Age
- BMI
- Activity level
- Goal delta (weight loss vs gain)
- Average sleep
- Average workout minutes

Includes automatic elbow/silhouette score evaluation, descriptive persona labeling,
artifact persistence via joblib, and inference via predict_cluster.
"""

import json
import logging
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from recommender.config import (
    CLUSTERING_META_PATH,
    KMEANS_MODEL_PATH,
    KMEANS_SCALER_PATH,
    RANDOM_SEED,
)
from recommender.features import (
    FEATURE_NAMES,
    build_feature_dataframe,
    extract_features_from_dict,
)

logger = logging.getLogger(__name__)

# Fallback labels if metadata is absent
DEFAULT_CLUSTER_LABELS = {
    0: "Beginner Weight-Loss",
    1: "Active Fitness & Maintenance",
    2: "High-Intensity Athlete",
    3: "Sedentary Wellness Starter",
}


def generate_cluster_labels(
    kmeans: KMeans, scaler: StandardScaler, feature_names: list[str]
) -> dict[int, str]:
    """Derive descriptive, plain-language persona labels based on unscaled cluster centroids."""
    centroids = scaler.inverse_transform(kmeans.cluster_centers_)
    labels = {}

    for cluster_idx, centroid in enumerate(centroids):
        centroid_dict = dict(zip(feature_names, centroid))
        bmi = centroid_dict["bmi"]
        goal_delta = centroid_dict["goal_delta"]
        activity = centroid_dict["activity_numeric"]
        workout_min = centroid_dict["avg_workout_min"]

        # Plain language label heuristics
        if goal_delta < -3.0:
            if activity <= 2.0:
                label = "Beginner Weight-Loss"
            else:
                label = "Active Fat-Loss & Conditioning"
        elif goal_delta > 1.5:
            label = "Muscle & Strength Gain"
        elif workout_min > 35 or activity >= 3.0:
            label = "High-Intensity Athlete"
        elif bmi > 27.0:
            label = "Gentle Lifestyle Recomposition"
        else:
            label = "Healthy Maintenance & Mobility"

        # Ensure uniqueness
        if label in labels.values():
            label = f"{label} (Group {cluster_idx + 1})"
        labels[cluster_idx] = label

    return labels


def find_best_k(
    X_scaled: np.ndarray,
    k_min: int = 3,
    k_max: int = 6,
    random_state: int = RANDOM_SEED,
) -> tuple[int, dict[int, float], dict[int, float]]:
    """Evaluate silhouette scores and inertias across candidate k values."""
    inertias = {}
    silhouettes = {}
    best_k = k_min
    best_sil = -1.0

    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        km.fit(X_scaled)
        inertias[k] = float(km.inertia_)
        sil = float(silhouette_score(X_scaled, km.labels_))
        silhouettes[k] = sil
        if sil > best_sil:
            best_sil = sil
            best_k = k

    return best_k, inertias, silhouettes


def train_user_clusters(
    users_df: pd.DataFrame,
    logs_df: pd.DataFrame | None = None,
    n_clusters: int | None = None,
    save_artifacts: bool = True,
) -> dict[str, Any]:
    """Train KMeans clustering model and StandardScaler on user features.

    Returns:
        Dictionary with training metrics, silhouette score, chosen k, and cluster labels.
    """
    feature_df = build_feature_dataframe(users_df, logs_df)
    X = feature_df[FEATURE_NAMES].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if n_clusters is None:
        best_k, inertias, silhouettes = find_best_k(X_scaled, k_min=3, k_max=6)
        chosen_k = best_k
    else:
        chosen_k = n_clusters
        km_temp = KMeans(n_clusters=chosen_k, random_state=RANDOM_SEED, n_init=10).fit(
            X_scaled
        )
        inertias = {chosen_k: float(km_temp.inertia_)}
        silhouettes = {chosen_k: float(silhouette_score(X_scaled, km_temp.labels_))}

    kmeans = KMeans(n_clusters=chosen_k, random_state=RANDOM_SEED, n_init=10)
    kmeans.fit(X_scaled)

    final_silhouette = float(silhouette_score(X_scaled, kmeans.labels_))
    cluster_labels = generate_cluster_labels(kmeans, scaler, FEATURE_NAMES)

    meta = {
        "n_clusters": chosen_k,
        "silhouette_score": round(final_silhouette, 4),
        "feature_names": FEATURE_NAMES,
        "cluster_labels": {str(k): v for k, v in cluster_labels.items()},
        "inertias": inertias,
        "silhouettes": silhouettes,
    }

    if save_artifacts:
        joblib.dump(kmeans, KMEANS_MODEL_PATH)
        joblib.dump(scaler, KMEANS_SCALER_PATH)
        with open(CLUSTERING_META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    return meta


class UserClusterPredictor:
    """Predictor class for user cluster assignment."""

    def __init__(self) -> None:
        self.kmeans: KMeans | None = None
        self.scaler: StandardScaler | None = None
        self.meta: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if KMEANS_MODEL_PATH.exists() and KMEANS_SCALER_PATH.exists():
            try:
                self.kmeans = joblib.load(KMEANS_MODEL_PATH)
                self.scaler = joblib.load(KMEANS_SCALER_PATH)
                if CLUSTERING_META_PATH.exists():
                    with open(CLUSTERING_META_PATH, "r", encoding="utf-8") as f:
                        self.meta = json.load(f)
            except (OSError, KeyError, ValueError) as e:
                logger.warning(f"Could not load clustering artifacts: {e}")

    def predict(
        self, user_dict: dict[str, Any], logs: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Predict cluster index and descriptive persona label for a user."""
        vec = extract_features_from_dict(user_dict, logs).reshape(1, -1)
        feat_dict = dict(zip(FEATURE_NAMES, vec[0].tolist()))

        if self.kmeans is None or self.scaler is None:
            # Fallback heuristic if models not trained yet
            goal_delta = feat_dict["goal_delta"]
            cluster_id = 0 if goal_delta < 0 else 1
            return {
                "cluster_id": cluster_id,
                "cluster_label": DEFAULT_CLUSTER_LABELS.get(
                    cluster_id, "Standard Member"
                ),
                "features": feat_dict,
            }

        vec_scaled = self.scaler.transform(vec)
        cluster_id = int(self.kmeans.predict(vec_scaled)[0])

        cluster_labels_map = self.meta.get("cluster_labels", {})
        label = cluster_labels_map.get(
            str(cluster_id),
            DEFAULT_CLUSTER_LABELS.get(cluster_id, f"Cluster {cluster_id}"),
        )

        return {
            "cluster_id": cluster_id,
            "cluster_label": label,
            "features": feat_dict,
        }


# Singleton instance
_predictor_instance: UserClusterPredictor | None = None


def predict_cluster(
    user_dict: dict[str, Any], logs: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Exposed public function to predict cluster persona for a user."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = UserClusterPredictor()
    return _predictor_instance.predict(user_dict, logs)
