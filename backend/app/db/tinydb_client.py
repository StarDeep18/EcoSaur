import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from tinydb import TinyDB, Query
from app.core.config import settings

# Initialize TinyDB using the path from config
db_path = settings.TINYDB_PATH
if not db_path:
    db_path = "ecosaur_db.json"

# Ensure the directory for the db exists
db_dir = os.path.dirname(os.path.abspath(db_path))
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

db = TinyDB(db_path)
scans_table = db.table("scans")
users_table = db.table("users")

# Helper functions for SCANS (Scan History)
def save_scan(
    corrected_text: str,
    score: int,
    grade: str,
    explanation: str,
    alternative: Dict[str, Any],
    breakdown: List[Dict[str, Any]],
    user_id: str = "default"
) -> Dict[str, Any]:
    """
    Save a food analysis scan document to TinyDB.
    """
    scan_id = str(uuid.uuid4())
    scan_doc = {
        "id": scan_id,
        "user_id": user_id,
        "date": datetime.utcnow().isoformat(),
        "corrected_text": corrected_text,
        "score": score,
        "grade": grade,
        "explanation": explanation,
        "alternative": alternative,
        "breakdown": breakdown
    }
    scans_table.insert(scan_doc)
    return scan_doc

def get_scan_history(user_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get the scan history for a user, sorted by date in descending order.
    """
    UserQuery = Query()
    scans = scans_table.search(UserQuery.user_id == user_id)
    # Sort by date descending (latest first)
    scans.sort(key=lambda x: x.get("date", ""), reverse=True)
    return scans[:limit]

# Helper functions for USERS (Health Preferences)
def get_user_preferences(user_id: str = "default") -> Dict[str, Any]:
    """
    Retrieve user preferences (e.g. health mode).
    Defaults to health_mode='General' if user doesn't exist yet.
    """
    UserQuery = Query()
    user = users_table.get(UserQuery.id == user_id)
    if not user:
        # Default initialization
        default_pref = {
            "id": user_id,
            "health_mode": "General",
            "created_at": datetime.utcnow().isoformat()
        }
        users_table.insert(default_pref)
        return default_pref
    return user

def update_user_preferences(health_mode: str, user_id: str = "default") -> Dict[str, Any]:
    """
    Save or update the user's health mode preference (e.g. Weight Loss, Gym/Fitness, Diabetic Friendly, Child Friendly, General).
    """
    UserQuery = Query()
    user = users_table.get(UserQuery.id == user_id)
    
    if not user:
        new_user = {
            "id": user_id,
            "health_mode": health_mode,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        users_table.insert(new_user)
        return new_user
    else:
        users_table.update(
            {"health_mode": health_mode, "updated_at": datetime.utcnow().isoformat()},
            UserQuery.id == user_id
        )
        return {**user, "health_mode": health_mode}
