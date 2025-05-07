from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

# Create a Pydantic model for the input data structure
class MatchRequest(BaseModel):
    skills: list[str]
    location: str

app = FastAPI()

# Allow access from anywhere (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT-Ar35mOmUWVi7sxlukLJLKtJ3WhtSx_dgEeB4GbNbOUAeTNKO0roiwUreM3sXFTnhlbRGM14yMqEP/pub?output=csv"  # Replace this!

@app.post("/match_trainers")
async def match_trainers(request: MatchRequest):
    # Access user skills and location from the request body
    user_skills = request.skills
    user_location = request.location

    # Fetch CSV data from the Google Sheet
    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    matched = []
    for _, row in df.iterrows():
        skills = str(row["Skills Taught"]).lower().split(",")
        city = str(row["City"]).lower()
        membership = str(row.get("Membership Type", "Free")).lower()

        # Check if there is a skill match and location match
        skill_match = any(skill.strip().lower() in [s.strip() for s in skills] for skill in user_skills)
        location_match = not user_location or user_location.lower() in city

        # Assign score based on membership type
        if skill_match and location_match:
            score = 2 if membership == "paid" else 1
            matched.append((score, row))

    # Sort by score (highest first)
    matched.sort(key=lambda x: x[0], reverse=True)

    # Return the top 10 matches
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
