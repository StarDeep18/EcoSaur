import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.database_models import User, Product, Scan, ModerationQueue, RecommendationLog

def save_scan(
    db: Session,
    corrected_text: str,
    score: int,
    grade: str,
    explanation: str,
    alternative: Dict[str, Any],
    breakdown: List[Dict[str, Any]],
    user_id: str = "default",
    confidence_ocr: float = 1.0,
    confidence_match: float = 1.0,
    confidence_analysis: float = 1.0,
    confidence_rec: float = 1.0
) -> Scan:
    """
    Save a food analysis scan document directly to SQLite via SQLAlchemy.
    """
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
        breakdown_json=json.dumps(breakdown),
        confidence_ocr=confidence_ocr,
        confidence_match=confidence_match,
        confidence_analysis=confidence_analysis,
        confidence_rec=confidence_rec
    )
    db.add(scan_doc)
    db.commit()
    db.refresh(scan_doc)
    return scan_doc

def get_scan_history(db: Session, user_id: str = "default", limit: int = 50) -> List[Scan]:
    """
    Get the scan history for a user, sorted by date in descending order.
    """
    return db.query(Scan).filter(Scan.user_id == user_id).order_by(Scan.date.desc()).limit(limit).all()

def get_user_preferences(db: Session, user_id: str = "default") -> User:
    """
    Retrieve user preferences (e.g. health mode).
    Defaults to health_mode='General' if user doesn't exist yet.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, health_mode="General")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def update_user_preferences(db: Session, health_mode: str, user_id: str = "default") -> User:
    """
    Save or update the user's health mode preference.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, health_mode=health_mode)
        db.add(user)
    else:
        user.health_mode = health_mode
        user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

def get_custom_barcode(db: Session, barcode: str) -> Optional[Product]:
    """
    Search our local crowdsourced database moat for a barcode.
    """
    return db.query(Product).filter(Product.barcode == barcode.strip()).first()

def save_custom_barcode(
    db: Session, 
    barcode: str, 
    product_name: str, 
    ingredients_text: str, 
    user_id: str = "default"
) -> Product:
    """
    Saves a user-submitted crowdsourced product barcode permanently into our database moat.
    """
    existing = db.query(Product).filter(Product.barcode == barcode.strip()).first()
    if existing:
        existing.product_name = product_name.strip()
        existing.ingredients_text = ingredients_text.strip()
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        prod = existing
    else:
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
    return prod

def queue_unknown_ingredient(db: Session, name: str) -> None:
    """
    Queues unrecognized ingredients into a moderation table for administrator review,
    improving spelling correction mapping continuously.
    """
    name_clean = name.strip().lower()
    if not name_clean:
        return
        
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

def queue_unknown_ingredient_standalone(name: str) -> None:
    """
    Standalone local database session wrapper allowing background text processing tools
    to log items securely without sharing request session lifecycles.
    """
    db = SessionLocal()
    try:
        queue_unknown_ingredient(db, name)
    except Exception as e:
        db.rollback()
        print(f"Warning: Standalone unknown ingredient queuing failed: {e}")
    finally:
        db.close()
