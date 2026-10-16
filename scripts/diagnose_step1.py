import json
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv(".env")

print("--- 1.A: FOOD CLASSIFICATION DIAGNOSIS ---")
df = pd.read_csv("data/foods.csv")
print(f"data/foods.csv row count: {len(df)}")
print("CSV columns:", list(df.columns))
print("CSV diet_type counts:", df["diet_type"].value_counts(dropna=False).to_dict())

with open("data/foods.json", "r", encoding="utf-8") as f:
    foods_json = json.load(f)
print(f"data/foods.json count: {len(foods_json)}")
json_counts = {}
for x in foods_json:
    d = x.get("diet_type")
    json_counts[d] = json_counts.get(d, 0) + 1
print("JSON diet_type counts:", json_counts)

# Check MongoDB foods collection
from pymongo import MongoClient
import certifi

mongo_uri = os.environ.get("MONGODB_URI")
db_name = os.environ.get("MONGODB_DB_NAME", "myfitness")
client = MongoClient(
    mongo_uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000
)
db = client[db_name]
mongo_foods_count = db["foods"].count_documents({})
print(f"MongoDB 'foods' count: {mongo_foods_count}")

mongo_diet_types = db["foods"].aggregate(
    [{"$group": {"_id": "$diet_type", "count": {"$sum": 1}}}]
)
print("MongoDB foods diet_type counts:", list(mongo_diet_types))

# Check misclassifications
nonveg_keywords = [
    "chicken",
    "fish",
    "egg",
    "mutton",
    "prawn",
    "beef",
    "pork",
    "meat",
    "salmon",
    "tuna",
    "turkey",
    "lamb",
    "bacon",
]
print("\nChecking misclassified foods in CSV (contains nonveg keyword but marked veg):")
for idx, r in df.iterrows():
    name = str(r["name"]).lower()
    if r.get("diet_type") == "veg":
        for kw in nonveg_keywords:
            if kw in name:
                print(
                    f"  CSV #{idx} id={r.get('_id', r.get('id'))} name='{r['name']}' diet_type={r['diet_type']} keyword='{kw}'"
                )

# Check all food items in CSV to see what they are
print("\nAll items in CSV:")
for idx, r in df.iterrows():
    print(
        f"  {r.get('_id', r.get('id', idx))}: {r['name']} | diet_type={r.get('diet_type')}"
    )
