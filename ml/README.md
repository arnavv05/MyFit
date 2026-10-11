# Myfitness ML & Recommender System Package (Member B)

Production-ready machine learning package for **Myfitness**:
1. **Hybrid Exercise Recommender**: Item-based Collaborative Filtering (cosine similarity) + Latent Factor Matrix Factorization (TruncatedSVD) blended with K-Means cluster popularity, injury safety filtering, and Compendium MET calorie burn allocation.
2. **Food Recommender**: Item-based similarity + goal-specific macro-fit scoring with a **strict 100% vegetarian filter** (guaranteed in tests) and calorie-target portion scaling.
3. **K-Means User Clustering**: Unsupervised persona clustering ($k=3$) over age, BMI, activity level, goal delta, average sleep, and workout volume.
4. **Evaluation Pipeline**: Chronological time-split validation tracking Precision@K, Recall@K, and NDCG@K against popularity baselines.
5. **EDA Aggregates**: Exported figures and statistics for Member C's Streamlit analytics dashboard.

---

## 📁 Repository Layout

```
ml/
├── requirements.txt            # Pinned dependencies
├── pyproject.toml              # Build & package config (pip install -e ml/)
├── README.md                   # ML documentation & guide
├── recommender/                # Core ML package
│   ├── __init__.py             # Exports get_exercise_recs, get_food_recs, model_version
│   ├── config.py               # Paths, seeds, env vars, versioning
│   ├── data_access.py          # Unified BaseDataAccess (MongoDataAccess + CsvDataAccess)
│   ├── features.py             # User feature engineering for clustering
│   ├── clustering.py           # KMeans clustering, silhouette scoring, persona labeling
│   ├── popularity.py           # Cold start & cluster popularity baselines
│   ├── exercise_recs.py        # Item-CF + TruncatedSVD + injury safety hybrid
│   ├── food_recs.py            # Macro-fit scoring + item-CF + hard veg filter
│   ├── calories.py             # Compendium MET calorie calculations
│   ├── evaluation.py           # Precision@K, Recall@K, NDCG@K, time-based split
│   ├── forecast.py             # Weight goal date forecasting (Ridge regression)
│   └── anomaly.py              # Outlier detection (day-to-day jumps, MAD)
├── scripts/
│   ├── generate_synthetic_data.py   # Deterministic synthetic data generator (seed 42)
│   ├── train_all.py                 # Clustering model training pipeline
│   ├── evaluate.py                  # Benchmark evaluation script (pop vs hybrid)
│   └── export_eda_aggregates.py     # Exports aggregates for Member C's dashboard
├── notebooks/
│   └── 01_eda.ipynb                 # Clean EDA notebook (distributions, correlations, outliers)
├── models/                          # Persisted model artifacts (.joblib, metadata JSON)
└── tests/
    └── test_recommender.py          # Pytest test suite
```

---

## 🚀 Setup & Execution

From the project root:

```bash
# 1. Install dependencies
pip install -r ml/requirements.txt

# 2. Install ML package in editable mode
pip install -e ml/

# 3. Generate synthetic data (if starting from scratch)
python ml/scripts/generate_synthetic_data.py

# 4. Train KMeans user clustering model
python ml/scripts/train_all.py

# 5. Run offline recommender evaluation (generates docs/ml_report.md)
python ml/scripts/evaluate.py

# 6. Export dashboard aggregates for Member C
python ml/scripts/export_eda_aggregates.py

# 7. Run test suite
pytest ml/tests
```

---

## 🤝 Team Integration Contracts

### For Member A (FastAPI Backend)
Import and call the recommender functions directly:
```python
from recommender import get_exercise_recs, get_food_recs, model_version

# GET /api/v1/recommend/exercises?date=
exercise_recs = get_exercise_recs(user_id="usr_0001", n=4)
# Returns: [{exercise_id: str, name: str, duration_min: int, est_kcal: float, reason: str}]

# GET /api/v1/recommend/foods?date=
food_recs = get_food_recs(user_id="usr_0001", kcal_target=450.0, n=3)
# Returns: [{food_id: str, name: str, grams: float, kcal: float, macros: {protein_g, carbs_g, fat_g, fiber_g}, reason: str}]

# Model version to log in recommendations collection:
current_version = model_version

# Optional Analytics Helpers (for GET /analytics/me):
from recommender import forecast_goal_date, detect_weight_anomalies

forecast = forecast_goal_date(user_id="usr_0001")
# Returns: {"expected_date": "2026-11-15" | None, "days_remaining": 35 | None, "weekly_rate_kg": -0.6, "on_track": True, "message": "..."}

anomalies = detect_weight_anomalies(user_id="usr_0001")
# Returns: [{"date": "2026-09-09", "weight_kg": 75.2, "reason": "..."}]
```

### For Member C (Streamlit Dashboard)
All precomputed aggregates are saved in `data/eda_aggregates/`:
- `demographics_distribution.json` (user base breakdown, BMI classes, age distribution)
- `correlations_matrix.csv` (correlation between weight changes, sleep, water, workouts, deficit)
- `daily_metrics_summary.json` (daily sleep and hydration statistics)
- `exercise_popularity_summary.csv` (exercise interaction frequencies and ratings)
- `food_macros_summary.csv` (veg vs non-veg macro comparisons)
See `data/eda_aggregates/README.md` for full documentation and code snippets.
