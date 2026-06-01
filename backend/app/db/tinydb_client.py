import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.database_models import User, Product, Scan, ModerationQueue

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
    Save a food analysis scan document to SQLite.
    """
    db = SessionLocal()
    try:
        # Ensure user exists in SQL DB
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, health_mode="General")
            db.add(user)
            db.flush()
            
        scan_id = str(uuid.uuid4())
        scan_doc = Scan(
            id=scan_id,
            user_id=user_id,
            date=datetime.utcnow(),
            corrected_text=corrected_text,
            score=score,
            grade=grade,
            explanation=explanation,
            alternative_name=alternative.get("name", ""),
            alternative_recipe=alternative.get("recipe", ""),
            alternative_prep_time=alternative.get("prep_time_mins", 15),
            alternative_cost=alternative.get("approx_cost_inr", 40),
            breakdown_json=json.dumps(breakdown)
        )
        db.add(scan_doc)
        db.commit()
        
        return {
            "id": scan_id,
            "user_id": user_id,
            "date": scan_doc.date.isoformat(),
            "corrected_text": corrected_text,
            "score": score,
            "grade": grade,
            "explanation": explanation,
            "alternative": alternative,
            "breakdown": breakdown
        }
    except Exception as e:
        db.rollback()
        print(f"Error in SQLite save_scan: {e}")
        raise e
    finally:
        db.close()

def get_scan_history(user_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get the scan history for a user, sorted by date in descending order.
    """
    db = SessionLocal()
    try:
        scans = db.query(Scan).filter(Scan.user_id == user_id).order_by(Scan.date.desc()).limit(limit).all()
        result = []
        for s in scans:
            result.append({
                "id": s.id,
                "user_id": s.user_id,
                "date": s.date.isoformat() if isinstance(s.date, datetime) else str(s.date),
                "corrected_text": s.corrected_text,
                "score": s.score,
                "grade": s.grade,
                "explanation": s.explanation,
                "alternative": {
                    "name": s.alternative_name,
                    "recipe": s.alternative_recipe,
                    "prep_time_mins": s.alternative_prep_time or 15,
                    "approx_cost_inr": s.alternative_cost or 40
                },
                "breakdown": json.loads(s.breakdown_json) if s.breakdown_json else []
            })
        return result
    finally:
        db.close()

# Helper functions for USERS (Health Preferences)
def get_user_preferences(user_id: str = "default") -> Dict[str, Any]:
    """
    Retrieve user preferences (e.g. health mode).
    Defaults to health_mode='General' if user doesn't exist yet.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, health_mode="General")
            db.add(user)
            db.commit()
            db.refresh(user)
        return {
            "id": user.id,
            "health_mode": user.health_mode,
            "created_at": user.created_at.isoformat() if isinstance(user.created_at, datetime) else str(user.created_at)
        }
    finally:
        db.close()

def update_user_preferences(health_mode: str, user_id: str = "default") -> Dict[str, Any]:
    """
    Save or update the user's health mode preference.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, health_mode=health_mode)
            db.add(user)
        else:
            user.health_mode = health_mode
            user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return {
            "id": user.id,
            "health_mode": user.health_mode,
            "updated_at": user.updated_at.isoformat() if isinstance(user.updated_at, datetime) else str(user.updated_at)
        }
    except Exception as e:
        db.rollback()
        print(f"Error updating user preferences: {e}")
        raise e
    finally:
        db.close()

def get_custom_barcode(barcode: str) -> Optional[Dict[str, Any]]:
    """
    Search our local crowdsourced database moat for a barcode.
    """
    db = SessionLocal()
    try:
        prod = db.query(Product).filter(Product.barcode == barcode.strip()).first()
        if prod:
            return {
                "barcode": prod.barcode,
                "product_name": prod.product_name,
                "ingredients_text": prod.ingredients_text,
                "user_id": prod.contributor_id,
                "created_at": prod.created_at.isoformat() if isinstance(prod.created_at, datetime) else str(prod.created_at),
                "verified": prod.verified,
                "upvotes": prod.upvotes
            }
        return None
    finally:
        db.close()

def save_custom_barcode(barcode: str, product_name: str, ingredients_text: str, user_id: str = "default") -> Dict[str, Any]:
    """
    Saves a user-submitted crowdsourced product barcode permanently into our database moat.
    """
    db = SessionLocal()
    try:
        # Check if already exists to prevent duplicates
        existing = db.query(Product).filter(Product.barcode == barcode.strip()).first()
        if existing:
            existing.product_name = product_name.strip()
            existing.ingredients_text = ingredients_text.strip()
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            prod = existing
        else:
            # Ensure contributor user exists in SQL DB
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(id=user_id, health_mode="General")
                db.add(user)
                db.flush()
                
            prod = Product(
                barcode=barcode.strip(),
                product_name=product_name.strip(),
                ingredients_text=ingredients_text.strip(),
                contributor_id=user_id,
                verified=False,
                upvotes=0
            )
            db.add(prod)
            db.commit()
            db.refresh(prod)
            
        return {
            "barcode": prod.barcode,
            "product_name": prod.product_name,
            "ingredients_text": prod.ingredients_text,
            "user_id": prod.contributor_id,
            "created_at": prod.created_at.isoformat() if isinstance(prod.created_at, datetime) else str(prod.created_at),
            "verified": prod.verified,
            "upvotes": prod.upvotes
        }
    except Exception as e:
        db.rollback()
        print(f"Error saving barcode: {e}")
        raise e
    finally:
        db.close()

def queue_unknown_ingredient(name: str) -> None:
    """
    Queues unrecognized ingredients into a moderation table for administrator review,
    improving spelling correction mapping continuously.
    """
    db = SessionLocal()
    try:
        name_clean = name.strip().lower()
        if not name_clean:
            return
            
        # Check if already queued
        existing = db.query(ModerationQueue).filter(
            ModerationQueue.item_type == "ingredient",
            ModerationQueue.item_id == name_clean
        ).first()
        
        if existing:
            data = json.loads(existing.item_data_json)
            data["count"] = data.get("count", 1) + 1
            data["last_scanned"] = datetime.utcnow().isoformat()
            existing.item_data_json = json.dumps(data)
            existing.updated_at = datetime.utcnow()
        else:
            queue_item = {
                "name": name_clean,
                "count": 1,
                "first_scanned": datetime.utcnow().isoformat(),
                "last_scanned": datetime.utcnow().isoformat()
            }
            moderation_entry = ModerationQueue(
                item_type="ingredient",
                item_id=name_clean,
                item_data_json=json.dumps(queue_item),
                status="pending"
            )
            db.add(moderation_entry)
            
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: queue_unknown_ingredient failed: {e}")
    finally:
        db.close()
