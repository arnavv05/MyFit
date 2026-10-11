"""Training pipeline script for K-Means user clustering and models.

Loads user data and daily logs from CSV or MongoDB, trains StandardScaler and
K-Means clustering, evaluates silhouette score across k=3..6, assigns plain-language
personas, and saves joblib artifacts to ml/models/.
"""

import sys
from pathlib import Path

import pandas as pd

# Add ml folder to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

from recommender.clustering import train_user_clusters
from recommender.config import DAILY_LOGS_CSV, USERS_CSV


def run_training() -> None:
    print("=== Training KMeans User Clustering ===")
    if not USERS_CSV.exists():
        print(f"Error: {USERS_CSV} not found! Run generate_synthetic_data.py first.")
        sys.exit(1)

    users_df = pd.read_csv(USERS_CSV)
    logs_df = pd.read_csv(DAILY_LOGS_CSV) if DAILY_LOGS_CSV.exists() else None

    print(
        f"Loaded {len(users_df)} users, {len(logs_df) if logs_df is not None else 0} daily logs."
    )
    results = train_user_clusters(
        users_df=users_df, logs_df=logs_df, save_artifacts=True
    )

    print("\nTraining complete! Results:")
    print(f"- Selected Clusters (k): {results['n_clusters']}")
    print(f"- Silhouette Score: {results['silhouette_score']:.4f}")
    print("- Personas Assigned:")
    for cid, label in results["cluster_labels"].items():
        print(f"  Cluster {cid}: {label}")


if __name__ == "__main__":
    run_training()
