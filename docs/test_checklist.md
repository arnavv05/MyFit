# Myfitness Full QA Manual Test Checklist

This checklist documents end-to-end test cases with preconditions, test steps, and expected results across all screens and user flows.

---

## Test Suite Summary

| ID | Test Case | Component / Screen | Priority |
|---|---|---|:---:|
| **TC-01** | User Registration with Validation | `/auth/register` (RegisterPage) | P0 |
| **TC-02** | User Login & JWT Persistence | `/auth/login` (LoginPage) | P0 |
| **TC-03** | Profile & Goal Onboarding | `/users/me` (OnboardingPage) | P0 |
| **TC-04** | Daily Log Submission with Catalog Search | `/logs` (DailyLogPage) | P0 |
| **TC-05** | Exercise & Food Recommendations | `/recommend` (RecommendationsPage) | P0 |
| **TC-06** | Recommendation Feedback Submission | `/feedback` (RecommendationsPage) | P1 |
| **TC-07** | Progress Analytics, Forecast & Anomalies | `/analytics/me` (ProgressPage) | P0 |
| **TC-08** | Diet Safety Filtering (Veg vs Nonveg) | `/recommend/foods` | P0 |
| **TC-09** | Injury Exclusion Verification | `/recommend/exercises` | P0 |
| **TC-10** | Population & User Streamlit Dashboard | `/dashboard` (Streamlit App) | P1 |
| **TC-11** | Mobile Responsiveness & Accessibility | CSS Layout & ARIA tags | P1 |

---

## Detailed Test Cases

### TC-01: User Registration
- **Preconditions**: Backend running on port 8000; MongoDB connected.
- **Steps**:
  1. Navigate to `http://localhost:5173/#/register`.
  2. Attempt submission with empty email/password.
  3. Enter email `test_student@example.com` and mismatched passwords.
  4. Enter matching passwords (>= 6 chars) and submit.
- **Expected Results**:
  - Empty submission shows accessible error banner.
  - Password mismatch shows validation error alert.
  - Valid submission returns 201 Created, sets JWT in localStorage, and navigates to `#/onboarding`.

### TC-02: User Login & Session Handling
- **Preconditions**: User registered from TC-01.
- **Steps**:
  1. Navigate to `http://localhost:5173/#/login`.
  2. Enter incorrect password.
  3. Enter valid credentials and submit.
  4. Simulate 401 Unauthorized token expiry.
- **Expected Results**:
  - Invalid credentials shows friendly error banner.
  - Valid credentials stores JWT and transitions user to `#/daily-log`.
  - 401 response clears token and smoothly redirects to login.

### TC-03: Profile Onboarding & Biometrics
- **Preconditions**: Authenticated user.
- **Steps**:
  1. Navigate to `http://localhost:5173/#/onboarding`.
  2. Change age, gender, height, weight, activity level, and diet type.
  3. Add injuries ("knee", "lower back").
  4. Set target weight and goal date.
  5. Click Save.
- **Expected Results**:
  - BMR and TDEE calculate dynamically on the screen.
  - Saving sends `PUT /users/me` with validated numbers.
  - Success message displays and user is navigated to Daily Log.

### TC-04: Daily Log Submission & Catalog Search
- **Preconditions**: Catalog seeded on backend.
- **Steps**:
  1. Navigate to `http://localhost:5173/#/daily-log`.
  2. Enter morning weight, sleep hours, water intake.
  3. In the Workouts section, type into the search box (e.g. "cycle" or "pushup").
  4. Select matching exercise, enter duration, and add workout.
  5. In the Meals section, type into the search box (e.g. "oat" or "egg").
  6. Select matching food item, enter grams, and add meal.
  7. Submit the daily log.
- **Expected Results**:
  - Search input filters dropdown choices in real time.
  - Form computes MET calorie burn and nutrition portion accurately.
  - `POST /logs` returns 200 with server-computed `kcal_in` and `kcal_out` displayed in summary cards.

### TC-05: Recommendations & Explainability
- **Preconditions**: Daily log saved.
- **Steps**:
  1. Navigate to `http://localhost:5173/#/recommendations`.
  2. Review Recommended Workouts cards.
  3. Review Recommended Meals cards.
- **Expected Results**:
  - Workouts display duration, estimated kcal burn, and visible "Why recommended" justification line.
  - Meals display portion grams, calories, macro breakdown (Protein, Carbs, Fat, Fiber), and dietary badge.

### TC-06: Recommendation Rating & Feedback
- **Steps**:
  1. On Recommendations page, click 1-5 star rating on an exercise card.
  2. Click 1-5 star rating on a food card.
- **Expected Results**:
  - Sends `POST /feedback` with `item_type`, `item_id`, and `rating`.
  - Star buttons update state with active styling (`aria-pressed="true"`).
  - Success alert confirms rating was recorded.

### TC-07: Progress Analytics, Forecast & Anomalies
- **Steps**:
  1. Navigate to `http://localhost:5173/#/progress`.
  2. Inspect Weight Trajectory sparkline chart vs Target Goal.
  3. Inspect Cumulative Calories In vs Out bar chart.
  4. Inspect Goal-Date Forecast card and Anomaly Warnings.
- **Expected Results**:
  - Goal reference line displays with target weight.
  - Active streak badge displays days logged.
  - Forecast card displays projected goal date, weekly velocity, and recommendation status.
  - Any detected anomalies (e.g., sharp weight drop or high calorie surplus) display with warning badges.

### TC-08: Vegetarian Diet Integrity
- **Preconditions**: User with `diet_type: "veg"`.
- **Steps**:
  1. Request `GET /recommend/foods` for vegetarian user.
  2. Verify all returned items.
- **Expected Results**:
  - 100% of recommended items have `diet_type == "veg"`. No meat, poultry, or fish appears.

### TC-09: Injury Safety Exclusions
- **Preconditions**: User has `injuries: ["knee"]`.
- **Steps**:
  1. Request `GET /recommend/exercises`.
  2. Cross-reference returned exercises with catalog `injury_flags`.
- **Expected Results**:
  - No exercise with `knee` in `injury_flags` is ever recommended. High-impact knee exercises (e.g., jump squats, barbell lunges) are strictly excluded.

### TC-10: Streamlit Dashboard Analytics
- **Preconditions**: Streamlit running on port 8501.
- **Steps**:
  1. Open `http://localhost:8501`.
  2. Review "Population Analytics": verify cluster distribution, cluster scatter, demographics, correlation heatmap, and popular items.
  3. Switch to "My Personal Analytics": enter user JWT token, check weight progress vs goal line, calorie balance, and sleep/water tracking.
- **Expected Results**:
  - All Plotly charts render smoothly without console errors.
  - Seamless fallback to offline EDA aggregates when live API is disconnected.

### TC-11: Responsive Layout & Accessibility
- **Steps**:
  1. Resize browser to 375px mobile viewport width.
  2. Navigate using keyboard `Tab` and `Shift+Tab`.
- **Expected Results**:
  - Layout stacks cards gracefully into single column with zero horizontal overflow.
  - All interactive elements have focus indicators and touch targets >= 44px.
  - Color contrast ratios exceed WCAG AA guidelines.
