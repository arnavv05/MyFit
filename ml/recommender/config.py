"""Configuration module for the Myfitness recommender package.

Handles directory paths, random seeds, model versioning, and environment variables.
"""

from pathlib import Path
from dotenv import load_dotenv

# Project root resolution (ml is at <root>/ml)
PACKAGE_ROOT = Path(__file__).resolve().parent
ML_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = ML_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = ML_ROOT / "models"

# Load root .env if present
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Ensure models directory exists

MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Model version tracking (exposed to Backend/Member A)
MODEL_VERSION = "0.1.0-kmeans-baseline"

# Reproducibility
RANDOM_SEED = 42

# Environment variables for database access
MONGO_URI_ENV = "MONGODB_URI"
MONGO_DB_NAME_ENV = "MONGODB_DB_NAME"
DEFAULT_MONGO_DB = "myfitness"

# Data file paths (CSV fallback)
EXERCISES_CSV = DATA_DIR / "exercises.csv"
FOODS_CSV = DATA_DIR / "foods.csv"
USERS_CSV = DATA_DIR / "users.csv"
DAILY_LOGS_CSV = DATA_DIR / "daily_logs.csv"
INTERACTIONS_CSV = DATA_DIR / "interactions.csv"

# Saved model paths
KMEANS_MODEL_PATH = MODELS_DIR / "kmeans_user_clusters.joblib"
KMEANS_SCALER_PATH = MODELS_DIR / "kmeans_scaler.joblib"
CLUSTERING_META_PATH = MODELS_DIR / "clustering_meta.json"
