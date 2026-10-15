"""End-to-End QA Smoke Test Walkthrough.

Walks through:
  1. Register
  2. Onboarding profile & goal setup (PUT /users/me)
  3. Daily log submission (POST /logs)
  4. View exercise & food recommendations (GET /recommend/exercises, GET /recommend/foods)
  5. Verify veg diet filter (0% non-veg) & injury safety exclusion (0% knee-flagged exercises)
  6. Submit feedback rating (POST /feedback)
  7. Retrieve personal progress analytics (GET /analytics/me with streak, forecast & anomalies)
  8. Retrieve population analytics (GET /analytics/population with clusters)
  9. Verify Streamlit dashboard chart generation
"""

import sys
import uuid
from pathlib import Path
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Ensure Windows terminal doesn't crash on unicode/emojis
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_URL = "http://127.0.0.1:8000/api/v1"


def run_full_qa_walkthrough():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    print("=" * 65)
    print("🚀 STARTING FULL END-TO-END QA SMOKE TEST WALKTHROUGH")
    print("=" * 65)

    # ---------------------------------------------------------
    # STEP 1: REGISTER
    # ---------------------------------------------------------
    unique_suffix = uuid.uuid4().hex[:6]
    email = f"qa_student_{unique_suffix}@myfitness.edu"
    password = "SecurePassword123"

    reg_payload = {"email": email, "password": password}
    r = client.post("/auth/register", json=reg_payload)
    print(f"\n[Step 1: Register] Status={r.status_code}")
    assert r.status_code == 201, f"Registration failed: {r.text}"
    user_data = r.json()
    user_id = user_data["_id"]
    print(f"  ✓ Registered User ID: {user_id}")
    print(f"  ✓ Email: {user_data['email']}")

    # ---------------------------------------------------------
    # STEP 2: LOGIN
    # ---------------------------------------------------------
    login_payload = {"email": email, "password": password}
    r = client.post("/auth/login", json=login_payload)
    print(f"\n[Step 2: Login] Status={r.status_code}")
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  ✓ JWT Token Acquired: {token[:20]}...")

    # ---------------------------------------------------------
    # STEP 3: ONBOARDING (PUT /users/me)
    # ---------------------------------------------------------
    onboarding_payload = {
        "profile": {
            "age": 22,
            "gender": "female",
            "height_cm": 165.0,
            "weight_kg": 62.0,
            "activity_level": "moderately_active",
            "diet_type": "veg",
            "injuries": ["knee"],
        },
        "goal": {
            "target_weight_kg": 58.0,
            "target_date": "2026-12-31",
        },
    }
    r = client.put("/users/me", json=onboarding_payload, headers=headers)
    print(f"\n[Step 3: Onboarding Profile] Status={r.status_code}")
    assert r.status_code == 200, f"Onboarding failed: {r.text}"
    updated_profile = r.json()
    assert updated_profile["profile"]["diet_type"] == "veg"
    assert "knee" in updated_profile["profile"]["injuries"]
    print(
        f"  ✓ Profile Saved: Diet=veg, Injuries={updated_profile['profile']['injuries']}"
    )
    print(
        f"  ✓ Goal Set: Target Weight={updated_profile['goal']['target_weight_kg']} kg"
    )

    # ---------------------------------------------------------
    # STEP 4: DAILY LOG (POST /logs)
    # ---------------------------------------------------------
    log_payload = {
        "date": "2026-10-15",
        "weight_kg": 61.8,
        "sleep_hours": 8.0,
        "water_ml": 2800.0,
        "workouts": [
            {
                "exercise_id": "ex_004",
                "duration_min": 30.0,
                "kcal_burned": 140.0,
                "rating": 5,
            }
        ],
        "meals": [
            {
                "food_id": "fd_001",
                "grams": 200.0,
                "kcal": 136.0,
            }
        ],
    }
    r = client.post("/logs", json=log_payload, headers=headers)
    print(f"\n[Step 4: Daily Log Submission] Status={r.status_code}")
    assert r.status_code in (200, 201), f"Daily log failed: {r.text}"
    daily_res = r.json()
    print(f"  ✓ Log Recorded for Date: {daily_res['date']}")
    print(
        f"  ✓ Server Caloric Rollup: kcal_in={daily_res['kcal_in']}, kcal_out={daily_res['kcal_out']}"
    )

    # ---------------------------------------------------------
    # STEP 5: RECOMMENDATIONS & SAFETY AUDIT
    # ---------------------------------------------------------
    r_ex = client.get("/recommend/exercises", headers=headers)
    print(f"\n[Step 5a: Exercise Recommendations] Status={r_ex.status_code}")
    assert r_ex.status_code == 200, f"Exercise recs failed: {r_ex.text}"
    ex_recs = r_ex.json()
    print(f"  ✓ Returned {len(ex_recs)} Exercise Recommendations")

    r_food = client.get("/recommend/foods", headers=headers)
    print(f"\n[Step 5b: Food Recommendations] Status={r_food.status_code}")
    assert r_food.status_code == 200, f"Food recs failed: {r_food.text}"
    food_recs = r_food.json()
    print(f"  ✓ Returned {len(food_recs)} Food Recommendations")

    # --- VERIFY RULE 7: STRICT VEG DIET INTEGRITY ---
    print("\n[Step 5c: Verifying Diet Integrity (Rule 7)]")
    # Fetch food catalog to inspect diet_type of recommended foods
    r_cat = client.get("/catalog")
    assert r_cat.status_code == 200
    catalog = r_cat.json()
    food_catalog_map = {f.get("_id") or f.get("id"): f for f in catalog["foods"]}
    ex_catalog_map = {e.get("_id") or e.get("id"): e for e in catalog["exercises"]}

    non_veg_detected = []
    for food in food_recs:
        fid = food.get("food_id")
        cat_item = food_catalog_map.get(fid)
        diet = cat_item.get("diet_type") if cat_item else food.get("diet_type", "veg")
        if diet != "veg":
            non_veg_detected.append((fid, food.get("name"), diet))

    assert (
        len(non_veg_detected) == 0
    ), f"EVIDENCE FAILURE: Non-veg foods found for veg user: {non_veg_detected}"
    print(
        f"  ✓ EVIDENCE PASS: 100% of {len(food_recs)} recommended foods conform to VEG diet."
    )
    for f in food_recs[:3]:
        print(
            f"    - {f.get('name')} ({f.get('grams')}g, {f.get('kcal')} kcal, why: '{f.get('reason')[:40]}...')"
        )

    # --- VERIFY RULE 7: STRICT INJURY EXCLUSION ---
    print("\n[Step 5d: Verifying Injury Exclusion (Rule 7)]")
    knee_flagged_detected = []
    for ex in ex_recs:
        eid = ex.get("exercise_id")
        cat_item = ex_catalog_map.get(eid)
        if cat_item and "knee" in [
            str(flag).lower() for flag in cat_item.get("injury_flags", [])
        ]:
            knee_flagged_detected.append(
                (eid, ex.get("name"), cat_item.get("injury_flags"))
            )

    assert (
        len(knee_flagged_detected) == 0
    ), f"EVIDENCE FAILURE: Knee-flagged exercises found: {knee_flagged_detected}"
    print(
        "  ✓ EVIDENCE PASS: 0% of exercises have 'knee' injury flags. Knee injury safely respected."
    )
    for ex in ex_recs[:3]:
        print(
            f"    - {ex.get('name')} (Duration: {ex.get('duration_min')}m, Est Burn: {ex.get('est_kcal')} kcal, reason: '{ex.get('reason')[:40]}...')"
        )

    # ---------------------------------------------------------
    # STEP 6: RECOMMENDATION FEEDBACK
    # ---------------------------------------------------------
    if ex_recs:
        target_ex = ex_recs[0]["exercise_id"]
        fb_ex = {"item_type": "exercise", "item_id": target_ex, "rating": 5}
        r = client.post("/feedback", json=fb_ex, headers=headers)
        assert r.status_code == 201
        print(f"\n[Step 6a: Exercise Feedback] Rated {target_ex} 5★ -> 201 Created")

    if food_recs:
        target_food = food_recs[0]["food_id"]
        fb_food = {"item_type": "food", "item_id": target_food, "rating": 4}
        r = client.post("/feedback", json=fb_food, headers=headers)
        assert r.status_code == 201
        print(f"[Step 6b: Food Feedback] Rated {target_food} 4★ -> 201 Created")

    # ---------------------------------------------------------
    # STEP 7: PERSONAL PROGRESS & TELEMETRY
    # ---------------------------------------------------------
    r_an = client.get("/analytics/me", headers=headers)
    print(f"\n[Step 7: Personal Progress Telemetry] Status={r_an.status_code}")
    assert r_an.status_code == 200
    me_analytics = r_an.json()
    print(f"  ✓ Total Workouts: {me_analytics.get('total_workouts_completed')}")
    print(f"  ✓ Active Streak: {me_analytics.get('streak', 1)} days")
    print(
        f"  ✓ Weight History: {len(me_analytics.get('weight_history', []))} data points"
    )
    forecast = me_analytics.get("forecast")
    if forecast:
        print(
            f"  ✓ Forecast: On-Track={forecast.get('on_track')}, Days to Goal={forecast.get('days_to_goal')}"
        )
    anomalies = me_analytics.get("anomalies", [])
    print(f"  ✓ Anomaly Check: {len(anomalies)} anomalies detected")

    # ---------------------------------------------------------
    # STEP 8: POPULATION ANALYTICS
    # ---------------------------------------------------------
    r_pop = client.get("/analytics/population")
    print(f"\n[Step 8: Population Analytics] Status={r_pop.status_code}")
    assert r_pop.status_code == 200
    pop_data = r_pop.json()
    print(f"  ✓ Total Population Users: {pop_data.get('total_users')}")
    print(f"  ✓ Clusters: {len(pop_data.get('clusters', []))} cluster archetypes")
    print(f"  ✓ Diet Distribution: {pop_data.get('diet_distribution')}")

    # ---------------------------------------------------------
    # STEP 9: STREAMLIT DASHBOARD INTEGRATION
    # ---------------------------------------------------------
    print("\n[Step 9: Streamlit Dashboard Chart Generators Verification]")
    from dashboard.charts import (
        create_weight_history_chart,
        create_user_calorie_balance_chart,
        create_sleep_water_chart,
        create_population_clusters_bar,
        create_cluster_scatter,
        create_popular_exercises_bar,
    )
    from dashboard.loaders import load_users_sample, load_exercise_popularity

    # Generate per-user charts with live data
    w_fig = create_weight_history_chart(
        me_analytics.get("weight_history", []), goal_weight_kg=58.0
    )
    assert len(w_fig.data) >= 1
    print("  ✓ Rendered Personal Weight Trajectory vs Goal Chart (Plotly Figure)")

    c_fig = create_user_calorie_balance_chart(
        me_analytics.get("total_kcal_in", 0), me_analytics.get("total_kcal_out", 0)
    )
    assert len(c_fig.data) == 1
    print("  ✓ Rendered Personal Calorie Balance Chart (Plotly Figure)")

    sw_fig = create_sleep_water_chart(me_analytics)
    assert len(sw_fig.data) == 2
    print("  ✓ Rendered Personal Sleep & Hydration Streak Chart (Plotly Figure)")

    # Generate population charts
    pop_clusters_fig = create_population_clusters_bar(pop_data.get("clusters", []))
    assert len(pop_clusters_fig.data) == 1
    print("  ✓ Rendered Population Cluster Distribution Chart (Plotly Figure)")

    users_df = load_users_sample(max_rows=100)
    scatter_fig = create_cluster_scatter(users_df)
    assert len(scatter_fig.data) >= 1
    print("  ✓ Rendered Population Cluster 2D Scatter Plot (Plotly Figure)")

    ex_df = load_exercise_popularity()
    ex_fig = create_popular_exercises_bar(ex_df, top_n=5)
    assert len(ex_fig.data) == 1
    print("  ✓ Rendered Popular Exercises Bar Chart (Plotly Figure)")

    print("\n" + "=" * 65)
    print("🏆 ALL 9 END-TO-END QA STEPS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    run_full_qa_walkthrough()
