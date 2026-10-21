import sys
from pathlib import Path
import streamlit as st

# Adding the repository root to sys.path ensures dashboard modules resolve in both IDE and Streamlit runners.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.api_client import fetch_population_analytics, fetch_user_analytics
from dashboard.charts import (
    create_activity_pie,
    create_bmi_pie,
    create_cluster_scatter,
    create_correlation_heatmap,
    create_daily_metrics_chart,
    create_gender_pie,
    create_macro_comparison_bar,
    create_popular_exercises_bar,
    create_popular_foods_bar,
    create_population_clusters_bar,
    create_sleep_water_chart,
    create_user_calorie_balance_chart,
    create_weight_history_chart,
)
from dashboard.loaders import load_popular_foods, load_users_sample

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
st.sidebar.subheader("Account Login")

if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = ""

with st.sidebar.expander("🔑 Quick Login / Sign In", expanded=not bool(st.session_state["auth_token"])):
    login_email = st.text_input("Email", value="student@myfitness.edu", key="dash_login_email")
    login_pwd = st.text_input("Password", value="password123", type="password", key="dash_login_pwd")
    if st.button("Sign In & Load Profile", use_container_width=True):
        try:
            import requests
            res = requests.post(
                "http://127.0.0.1:8000/api/v1/auth/login",
                json={"email": login_email, "password": login_pwd},
                timeout=5.0,
            )
            if res.status_code == 200:
                st.session_state["auth_token"] = res.json().get("access_token", "")
                st.sidebar.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.sidebar.error("Login failed. Check credentials.")
        except Exception as exc:
            st.sidebar.error(f"Cannot reach API: {exc}")

if st.session_state["auth_token"]:
    api_token = st.session_state["auth_token"]
    if st.sidebar.button("Log Out"):
        st.session_state["auth_token"] = ""
        st.rerun()
else:
    api_token = st.sidebar.text_input(
        "Or Paste Bearer Token / User ID", type="password"
    )

if st.sidebar.button("🔄 Refresh Live Data"):
    st.rerun()


if view_mode == "Population Analytics":
    pop_data, is_live = fetch_population_analytics()
    if is_live:
        st.sidebar.success("🟢 Connected to Live API")
    else:
        st.sidebar.info("🟡 Offline Fallback (EDA Aggregates)")

    st.title("💪 Myfitness Population Analytics")
    st.caption(
        "Live Population Analytics, K-Means Clustering & Aggregate Health Benchmarks"
    )

    # 1. Demographic Overview
    st.header("1. Demographics Overview")
    demo_data = pop_data.get("demographics", pop_data)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Users", f"{demo_data.get('total_users', 0):,}")
    col2.metric(
        "Mean Age", f"{demo_data.get('age_distribution', {}).get('mean', 0):.1f} yrs"
    )
    col3.metric(
        "Age Std Dev", f"{demo_data.get('age_distribution', {}).get('std', 0):.1f} yrs"
    )
    veg_pct = (
        demo_data.get("diet_type_ratio", {}).get("veg", 0)
        / max(demo_data.get("total_users", 1), 1)
        * 100
    )
    col4.metric("Vegetarian Users", f"{veg_pct:.1f}%")

    pie_col1, pie_col2, pie_col3 = st.columns(3)
    with pie_col1:
        st.plotly_chart(create_gender_pie(demo_data), use_container_width=True)
    with pie_col2:
        st.plotly_chart(create_bmi_pie(demo_data), use_container_width=True)
    with pie_col3:
        st.plotly_chart(create_activity_pie(demo_data), use_container_width=True)

    # 2. Population Clusters (Distribution & Scatter)
    st.header("2. Population Clusters (K-Means)")
    st.caption("Archetypes derived from biometric profiles and activity habits.")

    cl_col1, cl_col2 = st.columns(2)
    with cl_col1:
        # Cluster bar chart (live API or fallback)
        clusters = pop_data.get(
            "clusters",
            [
                {"cluster_id": 0, "name": "Sedentary High-BMI", "user_count": 280},
                {"cluster_id": 1, "name": "Active Maintenance", "user_count": 310},
                {"cluster_id": 2, "name": "Moderate Athletic", "user_count": 295},
                {"cluster_id": 3, "name": "Strength & Muscle Gain", "user_count": 180},
                {"cluster_id": 4, "name": "Endurance & Cardio", "user_count": 140},
            ],
        )
        st.plotly_chart(
            create_population_clusters_bar(clusters), use_container_width=True
        )

    with cl_col2:
        # Cluster scatter plot
        users_df = load_users_sample(max_rows=400)
        st.plotly_chart(create_cluster_scatter(users_df), use_container_width=True)

    # 3. Daily Metrics & Benchmarks
    st.header("3. Sleep & Hydration Benchmarks")
    daily_data = pop_data.get("daily_metrics", pop_data)

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric(
        "Avg Daily Sleep", f"{daily_data.get('sleep_hours', {}).get('mean', 0):.1f} hrs"
    )
    m_col2.metric(
        "Avg Daily Water", f"{daily_data.get('water_ml', {}).get('mean', 0):.0f} mL"
    )
    m_col3.metric(
        "Mean Calorie Balance", f"{daily_data.get('calorie_balance_mean', 0):.0f} kcal"
    )
    m_col4.metric("Total Logs", f"{daily_data.get('total_logs', 0):,}")

    st.plotly_chart(create_daily_metrics_chart(daily_data), use_container_width=True)

    # 4. Correlations Heatmap
    if "correlations" in pop_data:
        st.header("4. Metric Correlation Matrix")
        st.caption(
            "Pearson correlations between caloric deficit, hydration, sleep, and net weight loss."
        )
        st.plotly_chart(
            create_correlation_heatmap(pop_data["correlations"]),
            use_container_width=True,
        )

    # 5. Catalog Popularity (Exercises & Foods)
    st.header("5. Popular Catalog Items")
    pop_col1, pop_col2 = st.columns(2)

    with pop_col1:
        if "exercise_popularity" in pop_data:
            st.subheader("Top Exercises")
            top_n_ex = st.slider(
                "Number of exercises",
                min_value=5,
                max_value=20,
                value=8,
                step=1,
                key="ex_slider",
            )
            st.plotly_chart(
                create_popular_exercises_bar(
                    pop_data["exercise_popularity"], top_n=top_n_ex
                ),
                use_container_width=True,
            )

    with pop_col2:
        st.subheader("Top Foods")
        popular_foods_df = load_popular_foods(top_n=8)
        if not popular_foods_df.empty:
            st.plotly_chart(
                create_popular_foods_bar(popular_foods_df, top_n=8),
                use_container_width=True,
            )
        elif "food_macros" in pop_data:
            st.plotly_chart(
                create_macro_comparison_bar(pop_data["food_macros"]),
                use_container_width=True,
            )

else:
    # Per-user personal analytics view
    user_data, is_live = fetch_user_analytics(token_or_user_id=api_token)
    if is_live:
        st.sidebar.success("🟢 Authenticated Live Session")
    else:
        st.sidebar.info("🟡 Sample Benchmark Mode (Paste token for live data)")

    st.sidebar.markdown("---")
    goal_weight_target = st.sidebar.number_input(
        "Goal Target Weight (kg)",
        min_value=30.0,
        max_value=200.0,
        value=float(user_data.get("goal", {}).get("target_weight_kg", 69.0)),
        step=0.5,
    )

    st.title("👤 Personal Fitness Analytics")
    st.caption(
        "Real-time telemetry and trajectory tracking from `/api/v1/analytics/me`"
    )

    # KPI summary bar
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    streak_val = user_data.get("streak", user_data.get("total_days_logged", 0))
    kpi1.metric("Active Streak", f"🔥 {streak_val} days")
    kpi2.metric("Workouts Done", f"💪 {user_data.get('total_workouts_completed', 0)}")
    kpi3.metric("Avg Sleep", f"💤 {user_data.get('avg_sleep_hours', 0):.1f} hrs")
    kpi4.metric("Avg Water", f"💧 {user_data.get('avg_water_ml', 0):.0f} mL")
    net_cal = user_data.get("total_kcal_out", 0) - user_data.get("total_kcal_in", 0)
    kpi5.metric("Net Deficit", f"{net_cal:,.0f} kcal")

    # Goal Forecast Banner if available
    forecast = user_data.get("forecast")
    if forecast:
        status_color = "🟢" if forecast.get("on_track") else "🟡"
        st.info(
            f"{status_color} **Forecast Status:** {forecast.get('message', 'On track towards target goal weight.')}"
        )

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Weight Progress vs Target Goal")
        weight_history = user_data.get("weight_history", [])
        if weight_history:
            st.plotly_chart(
                create_weight_history_chart(
                    weight_history, goal_weight_kg=goal_weight_target
                ),
                use_container_width=True,
            )
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

    # Sleep & Water Consistency
    st.subheader("Recovery Consistency & Hydration Habit")
    st.plotly_chart(create_sleep_water_chart(user_data), use_container_width=True)

    # Anomaly alerts if any
    anomalies = user_data.get("anomalies", [])
    if anomalies:
        st.subheader("⚠️ Biometric & Caloric Anomalies")
        for ano in anomalies:
            st.warning(
                f"**[{ano.get('type', 'Alert')}]** {ano.get('message')} ({ano.get('date', 'Recent')})"
            )
