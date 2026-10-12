import sys
from pathlib import Path
import streamlit as st

# Why: Adding the repository root to sys.path ensures dashboard modules resolve in both IDE and Streamlit runners.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.loaders import (
    load_correlations,
    load_daily_metrics,
    load_demographics,
    load_exercise_popularity,
    load_food_macros,
)
from dashboard.charts import (
    create_activity_pie,
    create_bmi_pie,
    create_correlation_heatmap,
    create_daily_metrics_chart,
    create_gender_pie,
    create_macro_comparison_bar,
    create_popular_exercises_bar,
)

st.set_page_config(
    page_title="Myfitness Analytics Dashboard",
    page_icon="💪",
    layout="wide",
)

st.title("💪 Myfitness Population Analytics")
st.caption("Exploratory Data Analysis & Population Benchmarks (Aggregates)")

# 1. Demographics
st.header("1. Demographics Overview")
demo_data = load_demographics()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Users", f"{demo_data.get('total_users', 0):,}")
col2.metric("Mean Age", f"{demo_data.get('age_distribution', {}).get('mean', 0):.1f} yrs")
col3.metric("Age Std Dev", f"{demo_data.get('age_distribution', {}).get('std', 0):.1f} yrs")
veg_pct = demo_data.get("diet_type_ratio", {}).get("veg", 0) / max(demo_data.get("total_users", 1), 1) * 100
col4.metric("Vegetarian Users", f"{veg_pct:.1f}%")

pie_col1, pie_col2, pie_col3 = st.columns(3)
with pie_col1:
    st.plotly_chart(create_gender_pie(demo_data), use_container_width=True)
with pie_col2:
    st.plotly_chart(create_bmi_pie(demo_data), use_container_width=True)
with pie_col3:
    st.plotly_chart(create_activity_pie(demo_data), use_container_width=True)

# 2. Daily Metrics & Benchmarks
st.header("2. Sleep & Hydration Benchmarks")
daily_data = load_daily_metrics()

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("Avg Daily Sleep", f"{daily_data.get('sleep_hours', {}).get('mean', 0):.1f} hrs")
m_col2.metric("Avg Daily Water", f"{daily_data.get('water_ml', {}).get('mean', 0):.0f} mL")
m_col3.metric("Mean Calorie Balance", f"{daily_data.get('calorie_balance_mean', 0):.0f} kcal")
m_col4.metric("Total Logs", f"{daily_data.get('total_logs', 0):,}")

st.plotly_chart(create_daily_metrics_chart(daily_data), use_container_width=True)

# 3. Correlations Heatmap
st.header("3. Metric Correlation Matrix")
st.caption("Pearson correlations between caloric deficit, hydration, sleep, and net weight loss.")
corr_df = load_correlations()
st.plotly_chart(create_correlation_heatmap(corr_df), use_container_width=True)

# 4. Exercise Popularity
st.header("4. Popular Exercises")
top_n = st.slider("Number of exercises to show", min_value=5, max_value=20, value=10, step=1)
exercises_df = load_exercise_popularity()
st.plotly_chart(create_popular_exercises_bar(exercises_df, top_n=top_n), use_container_width=True)

# 5. Food Macro Comparison
st.header("5. Nutritional Macro Comparison")
st.caption("Average macronutrients per 100g comparing Vegetarian vs Non-Vegetarian food items.")
food_df = load_food_macros()
st.plotly_chart(create_macro_comparison_bar(food_df), use_container_width=True)
