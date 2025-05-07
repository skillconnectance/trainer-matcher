from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

# Allow access from anywhere (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/YOUR_SHEET_ID/pub?output=csv"  # Replace this!

@app.post("/match_trainers")
async def match_trainers(request: Request):
    data = await request.json()
    user_skills = data.get("skills", [])
    user_location = data.get("location", "")

    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    matched = []
    for _, row in df.iterrows():
        skills = str(row["Skills Taught"]).lower().split(",")
        city = str(row["City"]).lower()
        membership = str(row.get("Membership Type", "Free")).lower()

        skill_match = any(skill.strip().lower() in [s.strip() for s in skills] for skill in user_skills)
        location_match = not user_location or user_location.lower() in city

        if skill_match and location_match:
            score = 2 if membership == "paid" else 1
            matched.append((score, row))

    matched.sort(key=lambda x: x[0], reverse=True)

    return {
        "matches": [
            {
                "name": f"{r['First Name']} {r['Last Name']}",
                "city": r["City"],
                "skills": r["Skills Taught"],
                "membership": r["Membership Type"],
                "linkedin": r.get("LinkedIn Profile URL", ""),
                "bio": r.get("Short Bio", ""),
                "pic": r.get("Profile Picture Upload", ""),
            }
            for _, r in matched[:10]
        ]
    }
