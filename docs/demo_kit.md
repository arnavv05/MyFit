# 🎬 Myfitness 5-Minute Demo Script & Viva Kit

This document provides a step-by-step walkthrough script for live demonstrations, along with likely oral exam (Viva) questions and concise, technical answers for each module.

---

## ⏱️ 5-Minute Live Demo Script

### Preparation
1. Ensure the 3 services are running:
   - Backend API: `http://localhost:8000/docs`
   - Frontend: `http://localhost:5173`
   - Streamlit Dashboard: `http://localhost:8501`
2. Open Chrome/Edge at `http://localhost:5173`.

---

### Step 1: Registration (0:00 - 0:45)
- **Action**: Navigate to `http://localhost:5173/register`.
- **Inputs to Type**:
  - **Email**: `alex.viva@myfitness.edu`
  - **Password**: `VivaPass2026!`
- **Click**: `Create Account`.
- **Talking Point**: *"The client registers the user via `POST /auth/register`, immediately acquires a JWT via `POST /auth/login`, stores the token securely in client session storage, and routes seamlessly to onboarding."*

---

### Step 2: Onboarding & Profile Setup (0:45 - 1:30)
- **Action**: On `http://localhost:5173/onboarding`:
- **Inputs to Select & Type**:
  - **Age**: `25`
  - **Gender**: `Female`
  - **Height**: `168 cm`
  - **Weight**: `68.0 kg`
  - **Activity Level**: `Moderately Active (moderate exercise 3-5 days/wk)`
  - **Dietary Preference**: `Vegetarian` *(Crucial for safety filter demo)*
  - **Injuries**: Type `knee` and press **Add**
  - **Target Weight**: `62.0 kg`
  - **Target Date**: `2026-12-31`
  - **Primary Goal**: `Weight Loss`
- **Notice**: Real-time BMR and TDEE preview dynamically calculate using Mifflin-St Jeor:
  - $\text{BMR} \approx 1459\text{ kcal}$, $\text{TDEE} \approx 2261\text{ kcal}$.
- **Click**: `Save Profile & Get Started`.

---

### Step 3: Daily Biometric & Workout Log (1:30 - 2:30)
- **Action**: Automatically lands on `/daily-log` (or click **Daily Log** in nav).
- **Inputs to Type**:
  - **Today's Weight**: `67.8 kg`
  - **Sleep**: `7.5 hours`
  - **Water**: `2500 ml`
- **Log an Exercise via Catalog Search**:
  - Type `cycling` into the exercise search bar.
  - Select `Stationary Cycling (Light)` (MET: 5.5).
  - Duration: `30 min` $\rightarrow$ auto-computes $\approx 186\text{ kcal burned}$.
  - Click `Add Workout`.
- **Log a Meal via Catalog Search**:
  - Type `oats` or `chia` into the food search bar.
  - Select `Chia Seed Pudding` (180 kcal/100g).
  - Grams: `150 g` $\rightarrow$ auto-computes $270\text{ kcal}$.
  - Click `Add Meal`.
- **Click**: `Save Today's Log`.
- **Talking Point**: *"Notice the live catalog search with text indexes and the client-side MET calculation formula before posting to `/logs`."*

---

### Step 4: AI Recommendations & Feedback Loop (2:30 - 3:30)
- **Action**: Click **Recommendations** in the navbar (`/recommendations`).
- **Highlight Key Safety & Explainability Features**:
  1. **Strict Vegetarian Diet**: Point out that 100% of the suggested foods are vegetarian (e.g. *Soya Chunks, Whey Protein Shake, Chia Seed Pudding*). Non-veg items like chicken or tuna are completely excluded.
  2. **Knee Injury Safety Filter**: Point out that high-impact knee exercises (like *Jump Squats* or *Child's Pose*) are excluded. Safe items like *Stationary Cycling*, *Pushups*, or *Brisk Walking* are presented.
  3. **Explainability Line**: Point out the "Why recommended" badge on each card explaining the biological or caloric reasoning.
  4. **Active Feedback**: Click the **👍 5-star rating** on an exercise card.
- **Talking Point**: *"Submitting ratings immediately updates the user interaction matrix via `POST /feedback` for continuous learning."*

---

### Step 5: Progress Telemetry & Linear Forecast (3:30 - 4:15)
- **Action**: Click **Progress** in the navbar (`/progress`).
- **Showcase**:
  - **Weight Trajectory Chart**: Current weight curve vs. the dashed goal line ($62\text{ kg}$).
  - **Calorie Balance**: Caloric deficit / surplus tracking.
  - **Goal Date Forecast Card**: Displays target date projection based on Ridge regression.
  - **Anomaly Warning Banner**: Highlights that inputs are normal and within healthy rate of change.

---

### Step 6: Population Analytics Dashboard (4:15 - 5:00)
- **Action**: Switch tab to `http://localhost:8501` (Streamlit Dashboard).
- **Showcase**:
  1. **My Personal Analytics**: View the live user telemetry, sleep/hydration streaks, and calorie breakdown.
  2. **Population View**:
     - **Cluster Distribution**: 3 fitness archetypes (Beginner Weight-Loss, Muscle Gain, Active Conditioning).
     - **Cluster 2D Scatter Plot**: PCA projection showing user positioning relative to cluster centroids.
     - **Popular Exercises & Foods**: Aggregated counts across 1,200+ users.
     - **Offline Resilience**: Explain that if the backend API is disconnected, the dashboard automatically falls back to precomputed aggregates in `data/eda_aggregates/`.

---

## 🎓 Viva Questions & Technical Answers

### Module 1: Unsupervised Clustering (K-Means)
**Q1: Why choose K-Means and how was $k=3$ determined?**  
> **Answer**: K-Means offers rapid, deterministic centroid clustering suitable for real-time user segmentation. We evaluated $k \in [2, 6]$ using the Silhouette score and the Elbow method on the 6-dimensional standardized user feature vector (age, BMI, activity level, goal delta, sleep, workout minutes). $k=3$ provided the highest silhouette score ($0.1763$) and formed three clear human-interpretable personas: Beginner Weight-Loss, Muscle Gain, and Active Conditioning.

**Q2: How are clusters used in recommendations?**  
> **Answer**: Clusters solve the cold-start problem. When a new user has fewer than 5 historical interactions, the hybrid recommender falls back to cluster-popularity priors—recommending what similar users in that cluster found most effective.

---

### Module 2: Hybrid Recommender System
**Q3: Explain the hybrid recommender architecture.**  
> **Answer**: It blends three candidate generation components:
> 1. **Item-based Collaborative Filtering**: Cosine similarity across user rating vectors.
> 2. **Matrix Factorization (TruncatedSVD)**: Low-rank latent space decomposition to discover hidden preference patterns.
> 3. **Cluster Popularity Priors**: Baseline frequency weighting within the user's demographic cluster.
> The scores are blended, and items previously performed by the user in the active window are filtered to promote novelty.

**Q4: How does the system compute exercise durations and calorie burns?**  
> **Answer**: The system uses the Compendium of Physical Activities formula:
> $$\text{Kcal} = \text{MET} \times \text{Weight (kg)} \times \frac{\text{Duration (min)}}{60}$$
> Given a daily session target burn (20% of TDEE), the engine allocates durations between 15 and 60 minutes across $n$ recommended exercises so their total burn matches the session target.

---

### Module 3: Vegetarian Filter & Medical Safety
**Q5: How is the vegetarian constraint enforced?**  
> **Answer**: It is enforced as a **hard deterministic filter**, not a soft ML score. In both the backend API (`backend/app/api/v1/recommend.py`) and the ML package (`food_recs.py`), any food with `is_veg == False` is strictly rejected before ranking if the user's profile specifies `dietary_preference == 'veg'`. Automated tests assert 0.0% non-veg leakage.

**Q6: How does injury exclusion work?**  
> **Answer**: Each exercise has an `injury_flags` attribute (e.g. `knee;wrist;lower_back`). If any flag matches the user's logged injuries, the exercise is pruned from the candidate pool before scoring. For example, users with knee injuries will never receive *Child's Pose* or *Jump Squats*.

---

### Module 4: Offline Evaluation & Metrics
**Q7: Why does the Popularity Baseline have higher Recall@5 than the Hybrid model in offline evaluation?**  
> **Answer**: On synthetic time-split test data, users frequently repeat core baseline exercises (like brisk walking or pushups). The static popularity baseline continually predicts these high-frequency items, yielding high recall on repeated actions. The hybrid model intentionally penalizes previously logged items to encourage serendipitous discovery of new exercises, which offline metrics treat as false positives. In production, this trade-off is essential to prevent user boredom.

---

### Module 5: Backend & Database Engineering
**Q8: Why FastAPI and Async Motor over standard synchronous Flask/PyMongo?**  
> **Answer**: Fitness tracking involves high-frequency telemetry logging and concurrent catalog lookups. Asynchronous I/O via `asyncio` and `Motor` prevents database socket blocking, allowing the server to handle high concurrency with low memory footprint.

**Q9: What database indexes were created and why?**  
> **Answer**:
> - Unique compound index on `daily_logs (user_id, date)`: Enforces one canonical log per user per calendar day.
> - Unique index on `users (email)`: Prevents account duplication.
> - Text index on `exercises (name, category)` and `foods (name, category)`: Powers full-text search with sub-millisecond query latency.

---

### Module 6: Frontend & UI/UX
**Q10: How does the frontend handle API failures and authentication expiry?**  
> **Answer**: All requests flow through a unified Axios instance (`src/api/client.js`). If a request returns a `401 Unauthorized` (e.g., token expired after 24 hours), the client catches it, triggers an `auth:unauthorized` custom event, clears `localStorage`, and cleanly redirects to `/login` without crashing or showing raw error traces.
