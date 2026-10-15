import sys
from pathlib import Path
import plotly.graph_objects as go  # type: ignore[import-untyped]

# Why: Adding the repository root to sys.path ensures imports resolve regardless of test runner working directory.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.api_client import fetch_population_analytics, fetch_user_analytics
from dashboard.charts import (
    create_activity_pie,
    create_bmi_pie,
    create_correlation_heatmap,
    create_daily_metrics_chart,
    create_gender_pie,
    create_macro_comparison_bar,
    create_popular_exercises_bar,
    create_population_clusters_bar,
    create_user_calorie_balance_chart,
    create_weight_history_chart,
)
from dashboard.loaders import (
    load_correlations,
    load_daily_metrics,
    load_demographics,
    load_exercise_popularity,
    load_food_macros,
)


def test_create_gender_pie():
    data = load_demographics()
    fig = create_gender_pie(data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_bmi_pie():
    data = load_demographics()
    fig = create_bmi_pie(data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_activity_pie():
    data = load_demographics()
    fig = create_activity_pie(data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_correlation_heatmap():
    df = load_correlations()
    fig = create_correlation_heatmap(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_popular_exercises_bar():
    df = load_exercise_popularity()
    fig = create_popular_exercises_bar(df, top_n=5)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_macro_comparison_bar():
    df = load_food_macros()
    fig = create_macro_comparison_bar(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_daily_metrics_chart():
    data = load_daily_metrics()
    fig = create_daily_metrics_chart(data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_weight_history_chart():
    history = [
        {"date": "2026-10-01", "weight_kg": 75.0},
        {"date": "2026-10-05", "weight_kg": 74.2},
    ]
    fig = create_weight_history_chart(history)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_user_calorie_balance_chart():
    fig = create_user_calorie_balance_chart(kcal_in=2000.0, kcal_out=2400.0)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_population_clusters_bar():
    clusters = [
        {"cluster_id": 0, "name": "Active Youth", "user_count": 30},
        {"cluster_id": 1, "name": "Sedentary Cut", "user_count": 45},
    ]
    fig = create_population_clusters_bar(clusters)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_create_weight_history_chart_with_goal():
    history = [
        {"date": "2026-10-01", "weight_kg": 75.0},
        {"date": "2026-10-05", "weight_kg": 74.2},
    ]
    fig = create_weight_history_chart(history, goal_weight_kg=70.0)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # logged weight + target goal line


def test_create_sleep_water_chart():
    from dashboard.charts import create_sleep_water_chart

    user_data = {
        "avg_sleep_hours": 7.8,
        "avg_water_ml": 2800.0,
        "streak": 5,
        "total_days_logged": 5,
    }
    fig = create_sleep_water_chart(user_data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_create_cluster_scatter():
    import pandas as pd
    from dashboard.charts import create_cluster_scatter

    users_df = pd.DataFrame(
        [
            {
                "_id": "usr_1",
                "height_cm": 175,
                "weight_kg": 70,
                "cluster_id": "0",
                "age": 25,
            },
            {
                "_id": "usr_2",
                "height_cm": 180,
                "weight_kg": 80,
                "cluster_id": "1",
                "age": 30,
            },
        ]
    )
    fig = create_cluster_scatter(users_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_create_popular_foods_bar():
    import pandas as pd
    from dashboard.charts import create_popular_foods_bar

    foods_df = pd.DataFrame(
        [
            {"name": "Oatmeal", "interaction_count": 25},
            {"name": "Boiled Eggs", "interaction_count": 40},
        ]
    )
    fig = create_popular_foods_bar(foods_df, top_n=2)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_api_client_offline_fallback():
    # Calling without active server must gracefully fallback without crashing
    data, is_live = fetch_population_analytics(base_url="http://127.0.0.1:9999/api/v1")
    assert not is_live
    assert data["source"] == "offline_aggregates"

    user_data, user_live = fetch_user_analytics(
        token="", base_url="http://127.0.0.1:9999/api/v1"
    )
    assert not user_live
    assert user_data["source"] == "offline_fallback"
