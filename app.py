from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import logging

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Allow all origins for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT-Ar35mOmUWVi7sxlukLJLKtJ3WhtSx_dgEeB4GbNbOUAeTNKO0roiwUreM3sXFTnhlbRGM14yMqEP/pub?output=csv"

@app.post("/match_trainers")
async def match_trainers(request: Request):
    try:
        logging.info("Received request to match trainers.")
        
        data = await request.json()
        user_skills = [skill.strip().lower() for skill in data.get("skills", [])]
        user_location = data.get("location", "").strip().lower()

        logging.info(f"User skills: {user_skills}, User location: {user_location}")

        # Read the CSV from Google Sheets, but handle out-of-range floats or invalid data
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
        
        # Clean the data to prevent out-of-range errors by replacing any invalid float values
        df = df.applymap(lambda x: None if isinstance(x, float) and (x == float('inf') or x == float('-inf')) else x)

        matched = []
        for _, row in df.iterrows():
            trainer_skills_raw = str(row.get("Skills Taught", ""))
            trainer_skills = [s.strip().lower() for s in trainer_skills_raw.split(",")]
            trainer_city = str(row.get("City", "")).strip().lower()
            membership = str(row.get("Membership Type", "Free")).strip().lower()

            skill_match = any(user_skill in trainer_skills for user_skill in user_skills)
            location_match = user_location in trainer_city

            if skill_match and location_match:
                score = 2 if membership == "paid" else 1
                matched.append((score, row))

        matched.sort(key=lambda x: x[0], reverse=True)

        response = {
            "matches": [
                {
                    "name": f"{r['First Name']} {r['Last Name']}",
                    "city": r["City"],
                    "skills": r["Skills Taught"],
                    "membership": r.get("Membership Type", "Free"),
                    "linkedin": r.get("LinkedIn Profile URL", ""),
                    "bio": r.get("Short Bio", ""),
                    "pic": r.get("Profile Picture Upload", "")
                }
                for _, r in matched[:10]
            ]
        }
        logging.info(f"Matches found: {len(matched)}")
        return response
    
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"error": str(e)}
