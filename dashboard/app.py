import sys
from pathlib import Path
import streamlit as st

# Why: Adding the repository root to sys.path ensures dashboard modules resolve in both IDE and Streamlit runners.
REPO_ROOT = Path(__file__).resolve().parent.parent
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

st.set_page_config(
    page_title="Myfitness Analytics Dashboard",
    page_icon="💪",
    layout="wide",
)

# Sidebar: View Selection & Auth
st.sidebar.title("Navigation")
view_mode = st.sidebar.radio(
    "Choose View",
    ["Population Analytics", "My Personal Analytics"],
)

st.sidebar.markdown("---")
st.sidebar.subheader("API Connection")
api_token = st.sidebar.text_input("User Token (for /analytics/me)", type="password")


if view_mode == "Population Analytics":
    pop_data, is_live = fetch_population_analytics()
    if is_live:
        st.sidebar.success("🟢 Connected to Live API")
    else:
        st.sidebar.info("🟡 Offline Fallback (EDA Aggregates)")

    st.title("💪 Myfitness Population Analytics")
    st.caption("Live Population Analytics & Aggregate Health Benchmarks")

    # If live API returns cluster breakdown
    if "clusters" in pop_data and pop_data["clusters"]:
        st.header("Population Clusters (ML K-Means)")
        st.plotly_chart(create_population_clusters_bar(pop_data["clusters"]), use_container_width=True)

    # 1. Demographics Overview
    st.header("1. Demographics Overview")
    demo_data = pop_data.get("demographics", pop_data)

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
    daily_data = pop_data.get("daily_metrics", pop_data)

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Avg Daily Sleep", f"{daily_data.get('sleep_hours', {}).get('mean', 0):.1f} hrs")
    m_col2.metric("Avg Daily Water", f"{daily_data.get('water_ml', {}).get('mean', 0):.0f} mL")
    m_col3.metric("Mean Calorie Balance", f"{daily_data.get('calorie_balance_mean', 0):.0f} kcal")
    m_col4.metric("Total Logs", f"{daily_data.get('total_logs', 0):,}")

    st.plotly_chart(create_daily_metrics_chart(daily_data), use_container_width=True)

    # 3. Correlations Heatmap
    if "correlations" in pop_data:
        st.header("3. Metric Correlation Matrix")
        st.caption("Pearson correlations between caloric deficit, hydration, sleep, and net weight loss.")
        st.plotly_chart(create_correlation_heatmap(pop_data["correlations"]), use_container_width=True)

    # 4. Exercise Popularity
    if "exercise_popularity" in pop_data:
        st.header("4. Popular Exercises")
        top_n = st.slider("Number of exercises to show", min_value=5, max_value=20, value=10, step=1)
        st.plotly_chart(create_popular_exercises_bar(pop_data["exercise_popularity"], top_n=top_n), use_container_width=True)

    # 5. Food Macro Comparison
    if "food_macros" in pop_data:
        st.header("5. Nutritional Macro Comparison")
        st.caption("Average macronutrients per 100g comparing Vegetarian vs Non-Vegetarian food items.")
        st.plotly_chart(create_macro_comparison_bar(pop_data["food_macros"]), use_container_width=True)

else:
    # Per-user personal analytics view
    user_data, is_live = fetch_user_analytics(token=api_token)
    if is_live:
        st.sidebar.success("🟢 Authenticated Live Session")
    else:
        st.sidebar.info("🟡 Sample Benchmark Mode (Paste token for live data)")

    st.title("👤 Personal Fitness Analytics")
    st.caption("Real-time telemetry and trajectory tracking from `/api/v1/analytics/me`")

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Days Logged", user_data.get("total_days_logged", 0))
    kpi2.metric("Workouts Done", user_data.get("total_workouts_completed", 0))
    kpi3.metric("Avg Sleep", f"{user_data.get('avg_sleep_hours', 0):.1f} hrs")
    kpi4.metric("Avg Water", f"{user_data.get('avg_water_ml', 0):.0f} mL")
    net_cal = user_data.get("total_kcal_out", 0) - user_data.get("total_kcal_in", 0)
    kpi5.metric("Net Calorie Deficit", f"{net_cal:,.0f} kcal")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Weight Progress")
        weight_history = user_data.get("weight_history", [])
        if weight_history:
            st.plotly_chart(create_weight_history_chart(weight_history), use_container_width=True)
        else:
            st.info("No weight logs recorded yet.")

    with c2:
        st.subheader("Energy Expenditure Balance")
        st.plotly_chart(
            create_user_calorie_balance_chart(
                user_data.get("total_kcal_in", 0.0),
                user_data.get("total_kcal_out", 0.0),
            ),
            use_container_width=True,
        )
