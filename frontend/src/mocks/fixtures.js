/**
 * @file fixtures.js
 * @description Mock fixtures mirroring MongoDB collections and API contracts.
 */

export const mockUser = {
  id: 'usr_mock_001',
  email: 'student@myfitness.edu',
  profile: {
    age: 21,
    gender: 'male',
    height_cm: 176,
    weight_kg: 73.5,
    activity_level: 'moderately_active',
    diet_type: 'veg',
    injuries: ['Mild knee strain'],
  },
  goal: {
    target_weight_kg: 69.0,
    target_date: '2026-12-31',
  },
  cluster_id: 2,
  created_at: '2026-09-01T00:00:00Z',
}

export const mockCatalogExercises = [
  { id: 'ex_1', name: 'Brisk Walking', category: 'Cardio', met_value: 3.8, injury_flags: [] },
  { id: 'ex_2', name: 'Bodyweight Squats', category: 'Strength', met_value: 5.0, injury_flags: ['knee'] },
  { id: 'ex_3', name: 'Standard Push-ups', category: 'Strength', met_value: 6.0, injury_flags: ['wrist', 'shoulder'] },
  { id: 'ex_4', name: 'Stationary Cycling', category: 'Cardio', met_value: 6.8, injury_flags: [] },
  { id: 'ex_5', name: 'Surya Namaskar (Sun Salutation)', category: 'Yoga', met_value: 4.0, injury_flags: [] },
  { id: 'ex_6', name: 'Dumbbell Shoulder Press', category: 'Strength', met_value: 4.5, injury_flags: ['shoulder'] },
  { id: 'ex_7', name: 'Plank Hold', category: 'Core', met_value: 4.0, injury_flags: ['lower_back'] },
]

export const mockCatalogFoods = [
  { id: 'fd_1', name: 'Oatmeal with Almonds & Banana', diet_type: 'veg', kcal_per_100g: 130, protein_g: 5, carbs_g: 24, fat_g: 3, fiber_g: 4 },
  { id: 'fd_2', name: 'Paneer Tikka Salad', diet_type: 'veg', kcal_per_100g: 180, protein_g: 14, carbs_g: 6, fat_g: 12, fiber_g: 3 },
  { id: 'fd_3', name: 'Yellow Lentil Dal with Brown Rice', diet_type: 'veg', kcal_per_100g: 140, protein_g: 7, carbs_g: 22, fat_g: 2.5, fiber_g: 4 },
  { id: 'fd_4', name: 'Grilled Herb Chicken Breast', diet_type: 'nonveg', kcal_per_100g: 165, protein_g: 31, carbs_g: 0, fat_g: 3.6, fiber_g: 0 },
  { id: 'fd_5', name: 'Tofu & Broccoli Sauté', diet_type: 'veg', kcal_per_100g: 110, protein_g: 10, carbs_g: 5, fat_g: 6, fiber_g: 3 },
  { id: 'fd_6', name: 'Boiled Egg Whites (4 units)', diet_type: 'nonveg', kcal_per_100g: 52, protein_g: 11, carbs_g: 0.7, fat_g: 0.2, fiber_g: 0 },
]

export const mockExerciseRecommendations = [
  {
    exercise_id: 'ex_1',
    name: 'Brisk Walking (Outdoor/Treadmill)',
    duration_min: 35,
    est_kcal: 165,
    reason: 'Low impact on knee joints, ideal for steady aerobic baseline',
  },
  {
    exercise_id: 'ex_3',
    name: 'Standard Push-ups (3 sets of 12)',
    duration_min: 20,
    est_kcal: 120,
    reason: 'Upper-body compound strength exercise matching your cluster progression',
  },
  {
    exercise_id: 'ex_5',
    name: 'Surya Namaskar (Sun Salutation)',
    duration_min: 25,
    est_kcal: 105,
    reason: 'Promotes full-body mobility and core stability without joint overload',
  },
]

export const mockFoodRecommendations = [
  {
    food_id: 'fd_2',
    name: 'Paneer Tikka Salad with Greens',
    diet_type: 'veg',
    grams: 220,
    kcal: 396,
    macros: { protein_g: 30.8, carbs_g: 13.2, fat_g: 26.4, fiber_g: 6.6 },
    reason: 'Rich vegetarian protein to replenish muscle tissue after upper body workout',
  },
  {
    food_id: 'fd_5',
    name: 'Tofu & Broccoli Sauté with Garlic',
    diet_type: 'veg',
    grams: 250,
    kcal: 275,
    macros: { protein_g: 25.0, carbs_g: 12.5, fat_g: 15.0, fiber_g: 7.5 },
    reason: 'Micronutrient-dense antioxidant recovery meal with clean plant protein',
  },
  {
    food_id: 'fd_1',
    name: 'Oatmeal with Almonds & Banana',
    diet_type: 'veg',
    grams: 200,
    kcal: 260,
    macros: { protein_g: 10.0, carbs_g: 48.0, fat_g: 6.0, fiber_g: 8.0 },
    reason: 'Sustained complex carbs replenishing glycogen stores',
  },
]

export const mockDailyLogs = [
  {
    id: 'log_001',
    user_id: 'usr_mock_001',
    date: '2026-10-09',
    weight_kg: 74.0,
    sleep_hours: 7.5,
    water_ml: 2600,
    workouts: [
      { exercise_id: 'ex_1', duration_min: 30, kcal_burned: 140, rating: 4 },
    ],
    meals: [
      { food_id: 'fd_1', grams: 200, kcal: 260 },
      { food_id: 'fd_2', grams: 220, kcal: 396 },
    ],
    kcal_in: 1980,
    kcal_out: 2250,
  },
  {
    id: 'log_002',
    user_id: 'usr_mock_001',
    date: '2026-10-10',
    weight_kg: 73.7,
    sleep_hours: 8.0,
    water_ml: 3000,
    workouts: [
      { exercise_id: 'ex_3', duration_min: 25, kcal_burned: 150, rating: 5 },
    ],
    meals: [
      { food_id: 'fd_3', grams: 300, kcal: 420 },
      { food_id: 'fd_5', grams: 250, kcal: 275 },
    ],
    kcal_in: 2050,
    kcal_out: 2310,
  },
]

export const mockAnalyticsMe = {
  // Shape matches GET /analytics/me — see backend all_schemas.py
  total_days_logged: 6,
  total_workouts_completed: 12,
  total_kcal_in: 12150,
  total_kcal_out: 13330,
  avg_sleep_hours: 7.6,
  avg_water_ml: 2750,
  weight_history: [
    { date: '2026-10-06', weight_kg: 74.3 },
    { date: '2026-10-07', weight_kg: 74.1 },
    { date: '2026-10-08', weight_kg: 74.0 },
    { date: '2026-10-09', weight_kg: 74.0 },
    { date: '2026-10-10', weight_kg: 73.7 },
    { date: '2026-10-11', weight_kg: 73.5 },
  ],
}

export const mockAnalyticsPopulation = {
  total_users: 150,
  cluster_count: 4,
  clusters: [
    { cluster_id: 0, label: 'Sedentary Weight Loss', count: 48, avg_bmi: 27.2, avg_calorie_target: 1850 },
    { cluster_id: 1, label: 'High Activity Muscle Gain', count: 32, avg_bmi: 23.5, avg_calorie_target: 2700 },
    { cluster_id: 2, label: 'Moderate Fitness Maintenance', count: 45, avg_bmi: 24.1, avg_calorie_target: 2200 },
    { cluster_id: 3, label: 'Endurance & Mobility', count: 25, avg_bmi: 22.0, avg_calorie_target: 2350 },
  ],
  top_exercises: [
    { name: 'Brisk Walking', logs_count: 312 },
    { name: 'Standard Push-ups', logs_count: 285 },
    { name: 'Stationary Cycling', logs_count: 210 },
    { name: 'Surya Namaskar', logs_count: 195 },
  ],
  top_foods: [
    { name: 'Paneer Tikka Salad', logs_count: 260, diet_type: 'veg' },
    { name: 'Oatmeal with Almonds', logs_count: 240, diet_type: 'veg' },
    { name: 'Grilled Chicken Breast', logs_count: 215, diet_type: 'nonveg' },
    { name: 'Yellow Lentil Dal', logs_count: 190, diet_type: 'veg' },
  ],
}
