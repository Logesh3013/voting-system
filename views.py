from django.shortcuts import render, redirect
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["voting_db"]
votes_col = db["votes"]
meta_col = db["meta"]

# Admin password
ADMIN_PASSWORD = "admin123"

# -----------------------------
# Index View (Voting Page)
# -----------------------------
def index(request):
    meta = meta_col.find_one({})
    voting_closed = meta.get("voting_closed", False) if meta else False
    message = ""

    if request.method == "POST" and not voting_closed:
        name = request.POST.get("name")
        voter_id = request.POST.get("voter_id")
        candidate = request.POST.get("candidate")

        if not name or not voter_id or not candidate:
            message = "All fields are required."
        elif votes_col.find_one({"voter_id": voter_id}):
            message = "This Voter ID has already voted."
        else:
            # Record vote
            votes_col.insert_one({
                "name": name,
                "voter_id": voter_id,
                "candidate": candidate
            })
            message = f"Thank you {name}, your vote for {candidate} has been recorded."

    context = {
        "message": message,
        "voting_closed": voting_closed
    }
    return render(request, "index.html", context)

# -----------------------------
# View Results
# -----------------------------
def view_results(request):
    if request.method == "POST":
        password = request.POST.get("admin_password")

        if password == ADMIN_PASSWORD:
            # Close voting
            meta_col.update_one({}, {"$set": {"voting_closed": True}}, upsert=True)

            # Count votes
            vote_counts = {}
            for vote in votes_col.find():
                candidate = vote["candidate"]
                vote_counts[candidate] = vote_counts.get(candidate, 0) + 1

            # Determine winner(s)
            if vote_counts:
                max_votes = max(vote_counts.values())
                winners = [name for name, count in vote_counts.items() if count == max_votes]
            else:
                max_votes = 0
                winners = []

            context = {
                "vote_counts": vote_counts,
                "winners": winners,
                "max_votes": max_votes,
            }
            return render(request, "results.html", context)
        else:
            return render(request, "index.html", {"message": "Wrong admin password!"})

    return redirect("index")

# -----------------------------
# Reset Voting
# -----------------------------
def reset_voting(request):
    if request.method == "POST":
        # Clear votes and reopen voting
        votes_col.delete_many({})
        meta_col.update_one({}, {"$set": {"voting_closed": False}}, upsert=True)
        return redirect("index")
    return redirect("index")
