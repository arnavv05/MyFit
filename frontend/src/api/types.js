/**
 * @file types.js
 * @description Single source of truth for JSDoc API contracts and MongoDB collection models.
 * Matches section 3 & 4 of project contract.
 */

/**
 * @typedef {Object} UserProfile
 * @property {number} age
 * @property {'male' | 'female' | 'other'} gender
 * @property {number} height_cm
 * @property {number} weight_kg
 * @property {'sedentary' | 'lightly_active' | 'moderately_active' | 'very_active' | 'extra_active'} activity_level
 * @property {'veg' | 'nonveg'} diet_type
 * @property {string[]} injuries
 */

/**
 * @typedef {Object} UserGoal
 * @property {number} target_weight_kg
 * @property {string} target_date - ISO date string YYYY-MM-DD
 */

/**
 * @typedef {Object} User
 * @property {string} id - Normalised from backend `_id` by the API layer
 * @property {string} email
 * @property {UserProfile} profile
 * @property {UserGoal} goal
 * @property {number} [cluster_id]
 * @property {string} created_at
 */

/**
 * @typedef {Object} WorkoutEntry
 * @property {string} exercise_id
 * @property {string} [name]
 * @property {number} duration_min
 * @property {number} [kcal_burned]
 * @property {number} [rating] - 1 to 5
 */

/**
 * @typedef {Object} MealEntry
 * @property {string} food_id
 * @property {string} [name]
 * @property {number} grams
 * @property {number} [kcal]
 */

/**
 * @typedef {Object} DailyLog
 * @property {string} id
 * @property {string} user_id
 * @property {string} date - YYYY-MM-DD
 * @property {number} weight_kg
 * @property {number} sleep_hours
 * @property {number} water_ml
 * @property {WorkoutEntry[]} workouts
 * @property {MealEntry[]} meals
 * @property {number} kcal_in
 * @property {number} kcal_out
 */

/**
 * @typedef {Object} ExerciseRecommendation
 * @property {string} exercise_id
 * @property {string} name
 * @property {number} duration_min
 * @property {number} est_kcal
 * @property {string} reason
 */

/**
 * @typedef {Object} FoodMacros
 * @property {number} protein_g
 * @property {number} carbs_g
 * @property {number} fat_g
 * @property {number} fiber_g
 */

/**
 * @typedef {Object} FoodRecommendation
 * @property {string} food_id
 * @property {string} name
 * @property {'veg' | 'nonveg'} [diet_type] - TODO: not in backend FoodRecItem; derived from user diet setting until Member A adds it
 * @property {number} grams
 * @property {number} kcal
 * @property {FoodMacros} macros
 * @property {string} reason
 */

/**
 * @typedef {Object} FeedbackPayload
 * @property {'exercise' | 'food'} item_type
 * @property {string} item_id
 * @property {number} rating - 1 to 5
 */
