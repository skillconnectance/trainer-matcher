from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from typing import List

# Define the Pydantic model for input request
class MatchRequest(BaseModel):
    skills: List[str]  # List of skills
    location: str      # Location as a string

app = FastAPI()

# Allow CORS (cross-origin resource sharing) for all domains (temporary for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains for testing
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Replace this with your Google Sheet URL (ensure it's in CSV format)
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT-Ar35mOmUWVi7sxlukLJLKtJ3WhtSx_dgEeB4GbNbOUAeTNKO0roiwUreM3sXFTnhlbRGM14yMqEP/pub?output=csv" 

@app.post("/match_trainers")
async def match_trainers(request: MatchRequest):
    try:
        # Access user skills and location from the request body
        user_skills = request.skills
        user_location = request.location

        # Fetch the CSV from the Google Sheet
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

        matched = []
        for _, row in df.iterrows():
            skills = str(row["Skills Taught"]).lower().split(",")
            city = str(row["City"]).lower()
            membership = str(row.get("Membership Type", "Free")).lower()

            # Check if there's a skill match and location match
            skill_match = any(skill.strip().lower() in [s.strip() for s in skills] for skill in user_skills)
            location_match = not user_location or user_location.lower() in city

            # Assign a score based on the match and membership type
            if skill_match and location_match:
                score = 2 if membership == "paid" else 1
                matched.append((score, row))

        # Sort by score in descending order
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
