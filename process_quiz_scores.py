import os
from supabase import create_client
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch all submissions
response = supabase.table("patient_submissions").select("*").execute()
if response.data is None:
    print("No data found.")
    exit()

submissions = response.data

# Group by (username, attempt_time)
attempts = defaultdict(list)
for entry in submissions:
    username = entry["username"]
    answered_at = entry["answered_at"]
    key = (username, answered_at)
    attempts[key].append(entry)

# Group all attempts per user, sort by timestamp descending, pick 3 most recent
user_attempts = defaultdict(list)
for (username, ts), records in attempts.items():
    user_attempts[username].append({
        "timestamp": ts,
        "records": records
    })

# Prepare scores
quiz_score_records = []

for username, quizzes in user_attempts.items():
    # Sort by timestamp (desc = latest first), keep only top 3
    sorted_quizzes = sorted(quizzes, key=lambda x: x["timestamp"], reverse=True)[:3]
    # Sort again by timestamp ASC to assign quiz_id 1,2,3
    sorted_quizzes = sorted(sorted_quizzes, key=lambda x: x["timestamp"])
    
    for quiz_id, quiz in enumerate(sorted_quizzes, start=1):
        score = sum(1 for r in quiz["records"] if r["is_correct"])
        quiz_score_records.append({
            "quiz_id": quiz_id,
            "username": username,
            "attempt_time": quiz["timestamp"],
            "score": score
        })

# Optional: Clear old records before inserting
# supabase.table("quiz_scores").delete().neq("username", "").execute()

# Insert into quiz_scores
if quiz_score_records:
    insert_response = supabase.table("quiz_scores").insert(quiz_score_records).execute()
    if insert_response.data:
        print(f"Inserted {len(insert_response.data)} quiz score records.")
    else:
        print(f"Failed to insert scores: {insert_response}")
else:
    print("No quiz scores to insert.")