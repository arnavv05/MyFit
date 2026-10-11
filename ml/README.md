# Myfitness ML & Recommender System Package (Member B)

This package contains the ML engineering codebase for **Myfitness**:
1. Exercise recommendations via collaborative filtering + K-Means cluster popularity + MET calorie burn calculation.
2. Food recommendations via macro-fit scoring + strict dietary safety filtering (veg/nonveg).
3. Data access abstraction supporting both MongoDB and offline CSV fallback.

---

## 📁 Package Structure

```
ml/
├── requirements.txt            # Pinned Python dependencies
├── pyproject.toml              # Build & package config
├── README.md                   # Setup and usage guide
├── recommender/                # Core ML package
│   ├── __init__.py             # Exports get_exercise_recs, get_food_recs, model_version
│   ├── config.py               # Paths, seeds, env vars, versioning
│   ├── data_access.py          # MongoDataAccess + CsvDataAccess
│   ├── features.py             # Feature engineering for user clustering
│   ├── clustering.py           # KMeans clustering, silhouette tuning, cluster labels
│   ├── popularity.py           # Cold start & cluster popularity baselines
│   ├── exercise_recs.py        # CF + safety filter + MET duration allocation
│   ├── calories.py             # MET calorie calculations (Compendium of Physical Activities)
│   └── food_recs.py            # Macro-fit scoring + hard veg filter
├── scripts/
│   ├── generate_synthetic_data.py   # Deterministic synthetic data generator (seed 42)
│   └── train_all.py                 # Clustering model training pipeline
├── models/                     # Persisted model artifacts (.joblib, metadata)
└── tests/
    └── test_recommender.py     # Pytest test suite
```

---

## 🚀 Quickstart & Installation

From the repository root:

```bash
# 1. Install dependencies
pip install -r ml/requirements.txt

# 2. Install recommender package in editable mode
pip install -e ml/

# 3. Generate synthetic data (if not already generated)
python ml/scripts/generate_synthetic_data.py

# 4. Train KMeans user clustering model
python ml/scripts/train_all.py

# 5. Run test suite
pytest ml/tests
```

---

## 🤝 Shared API Contract (For Member A)

Member A's FastAPI backend imports and calls these functions directly:

```python
from recommender import get_exercise_recs, get_food_recs, model_version

# 1. Exercise recommendations
# Returns: [{exercise_id: str, name: str, duration_min: int, est_kcal: float, reason: str}]
exercise_recs = get_exercise_recs(user_id="usr_0001", n=4)

# 2. Food recommendations
# Returns: [{food_id: str, name: str, grams: float, kcal: float, macros: {protein_g, carbs_g, fat_g, fiber_g}, reason: str}]
food_recs = get_food_recs(user_id="usr_0001", kcal_target=450.0, n=3)

# 3. Model version tracking
print(model_version)
```
