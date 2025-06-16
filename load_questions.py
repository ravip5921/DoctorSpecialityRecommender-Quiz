import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client


# --- Supabase credentials ---
# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

with open("scenario_quiz_questions.json", "r") as f:
    scenario_questions = json.load(f)


# # Optional: Clear old records before inserting
# supabase.table("quiz_scores").delete().neq("username", "").execute()
supabase.table("patient_submissions").delete().neq("username", "").execute()
supabase.table("patient_questions").delete().neq("prompt", "").execute()

# --- Upload to Supabase ---
for patient_name,questions in scenario_questions.items():
    for q in questions:
        prompt = q["question"]
        options = q["options"]
        correct = int(q["answer"])

        insert_data = {
            "patient_name":patient_name,
            "prompt": prompt,
            "opt1": options[0] if len(options) > 0 else "",
            "opt2": options[1] if len(options) > 1 else "",
            "opt3": options[2] if len(options) > 2 else "",
            "opt4": options[3] if len(options) > 3 else "",
            "correct_index": correct
        }

        response = supabase.table("patient_questions").insert(insert_data).execute()

        if response:
            print(f"Inserted: {prompt}")