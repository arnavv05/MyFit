import sys
from pathlib import Path
import plotly.graph_objects as go  # type: ignore[import-untyped]

# Why: Adding the repository root to sys.path ensures imports resolve regardless of test runner working directory.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.charts import (
    create_activity_pie,
    create_bmi_pie,
    create_correlation_heatmap,
    create_daily_metrics_chart,
    create_gender_pie,
    create_macro_comparison_bar,
    create_popular_exercises_bar,
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
