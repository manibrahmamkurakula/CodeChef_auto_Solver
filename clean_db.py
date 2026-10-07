import json

with open("C:/Users/MANI BRAHMAM/CodeChef_auto_Solver/solutions_database.json", "r", encoding="utf-8") as f:
    db = json.load(f)

print(f"Total keys before cleanup: {len(db)}")

dirty_placeholders = [
    "# cook your dish here",
    "cook your dish here",
    "update the code below",
    "write your query here"
]

removed = []
for k in list(db.keys()):
    c = db[k]["code"].strip().lower()
    # If the stored code is just the default placeholder
    if any(p in c for p in dirty_placeholders) and len(c) < 50:
        removed.append(k)
        del db[k]

print(f"Removed {len(removed)} default placeholder entries: {removed}")
print(f"Remaining valid solutions: {len(db)}")

with open("C:/Users/MANI BRAHMAM/CodeChef_auto_Solver/solutions_database.json", "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print("Saved cleaned solutions_database.json!")
