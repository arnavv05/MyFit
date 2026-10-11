# Myfitness QA Manual Test Checklist

This checklist verifies the frontend user experience, accessibility, and integration with the `/api/v1` contract. Run this checklist prior to merging PRs or delivering weekly demos.

---

## 1. Authentication (`/auth`)
- [ ] **Login Form Validation**:
  - [ ] Submitting empty fields triggers an accessible alert (`Please provide both email and password`).
  - [ ] Valid credentials save the JWT token to `localStorage` via `authStorage.js` and update context.
  - [ ] Invalid credentials show a clear error banner without crashing the application.
- [ ] **Register Form**:
  - [ ] Requires valid email format and password matching confirmation.
  - [ ] Successful registration transitions automatically to the **Onboarding Profile** setup.
- [ ] **Session Expiry & 401 Handling**:
  - [ ] When the API returns a 401 Unauthorized status, the app clears the session and returns to login.

---

## 2. Onboarding & Profile Setup (`/users/me`)
- [ ] **Biometrics & Activity**:
  - [ ] Inputs for age, height, weight, activity level (sedentary, light, moderate, active, very active).
  - [ ] Toggle between Vegetarian and Non-Vegetarian diet preference.
  - [ ] Live preview updates for **BMR** and **Maintenance TDEE** via the Mifflin-St Jeor equation.
- [ ] **Injury Multi-Entry**:
  - [ ] Can type and add custom injuries.
  - [ ] Quick suggestion buttons (+ Knee strain, + Lower back, etc.) add tags with a single click.
  - [ ] Individual injury tags can be removed with the `×` button.
- [ ] **Goal Configuration**:
  - [ ] Set target weight (kg) and realistic target date.
  - [ ] Saving calls `PUT /users/me` and navigates smoothly to today's log.

---

## 3. Daily Logging (`/logs`)
- [ ] **Date Selection**:
  - [ ] Date picker defaults to today's date in `YYYY-MM-DD` format.
  - [ ] Selecting a previous date loads that date's logged entries if they exist.
- [ ] **Biometrics**:
  - [ ] Weight (kg), sleep hours, and water intake (ml).
- [ ] **Workouts**:
  - [ ] Select exercise from today's recommendations or the catalog (addressing Gap #4).
  - [ ] Enter duration in minutes and workout rating (1-5).
  - [ ] Workouts display in a list with estimated calorie burn (MET formula: $kcal = MET \times weight \times hours$).
- [ ] **Meals**:
  - [ ] Select food item from catalog with veg/non-veg badge indicator.
  - [ ] Enter grams consumed; displays calculated caloric contribution.
- [ ] **Submission & Server Rollup**:
  - [ ] Submitting calls `POST /logs`.
  - [ ] Displays server-calculated `kcal_in` and `kcal_out` rollups (read-only from response).

---

## 4. Recommendations & Explainability (`/recommend`, `/feedback`)
- [ ] **Exercise Recommendations**:
  - [ ] Displays exercises recommended by Collaborative Filtering + K-Means clustering.
  - [ ] Displays estimated calorie burn and duration.
  - [ ] Visible **"Why recommended"** badge/line explaining the reason (e.g. low joint impact for knee injury).
- [ ] **Food Recommendations**:
  - [ ] Food suggestions matching the calorie replenishment need.
  - [ ] Visible **VEG / NON-VEG badge** respecting user diet preference.
  - [ ] Macro breakdown (Protein, Carbs, Fat, Fiber).
- [ ] **Recommendation Feedback**:
  - [ ] 1 to 5 star rating buttons on each exercise and food card.
  - [ ] Submits rating to `POST /feedback` and shows temporary confirmation banner.

---

## 5. Progress & Analytics (`/analytics/me`, `/logs`)
- [ ] **Goal Tracking**:
  - [ ] Visual progress bar towards target weight.
  - [ ] Comparison of current weight vs starting and target weight.
- [ ] **Energy Balance**:
  - [ ] Daily comparison chart of calories consumed (`kcal_in`) vs calories burned (`kcal_out`).
- [ ] **Habit Streaks**:
  - [ ] Sleep and hydration weekly tracking metrics.

---

## 6. Accessibility & Mobile Responsiveness
- [ ] **Keyboard Navigation**:
  - [ ] All interactive elements (inputs, buttons, tabs) are reachable via `Tab` key with visible focus rings.
  - [ ] Dialogs and alerts can be closed using keyboard triggers.
- [ ] **Screen Reader Support**:
  - [ ] Form inputs have associated `<label>` elements with matching `htmlFor` / `id`.
  - [ ] Veg/Non-veg badges have `role="status"` and descriptive `aria-label`.
  - [ ] Alert banners have `role="alert"`.
- [ ] **Mobile Viewport**:
  - [ ] Tested on 375px mobile viewport: navbar collapses cleanly, card grids collapse to 1 column, tap targets are minimum 44px.
