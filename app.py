from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

# Allow access from anywhere (for testing purposes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow access from all domains
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# The URL for the public CSV link from Google Sheets
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT-Ar35mOmUWVi7sxlukLJLKtJ3WhtSx_dgEeB4GbNbOUAeTNKO0roiwUreM3sXFTnhlbRGM14yMqEP/pub?output=csv"

@app.post("/match_trainers")
async def match_trainers(request: Request):
    # Parse the incoming JSON request
    data = await request.json()
    user_skills = data.get("skills", [])  # List of skills from the user
    user_location = data.get("location", "")  # Location of the user

    # Read the Google Sheet CSV
    try:
        df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
    except Exception as e:
        return {"error": f"Failed to load CSV from Google Sheets: {str(e)}"}

    # Initialize list to store matched trainers
    matched = []

    # Loop through the trainers in the CSV to find matches
    for _, row in df.iterrows():
        skills = str(row["Skills Taught"]).lower().split(",")  # Split the skills string into a list
        city = str(row["City"]).lower()  # Normalize city to lowercase
        membership = str(row.get("Membership Type", "Free")).lower()  # Normalize membership type

        # Check if any of the user's skills match the trainer's skills
        skill_match = any(skill.strip().lower() in [s.strip() for s in skills] for skill in user_skills)
        location_match = not user_location or user_location.lower() in city  # Match location (if provided)

        # If both skill and location match, add this trainer to the list
        if skill_match and location_match:
            score = 2 if membership == "paid" else 1  # Give higher score to paid trainers
            matched.append((score, row))

    # Sort trainers by score (higher score first)
    matched.sort(key=lambda x: x[0], reverse=True)

    # Return the top 10 matched trainers
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
            for _, r in matched[:10]  # Return the top 10 matches
        ]
    }
