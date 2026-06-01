import os
import sys

# Set Python path to backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services import normalization_engine
from app.db.database import engine, Base

def run_normalization_tests():
    print("==================================================")
    print("STARTING EcoSaur DETERMINISTIC NORMALIZATION TESTS")
    print("==================================================")
    
    # Initialize database tables for standalone test context
    Base.metadata.create_all(bind=engine)

    # 1. Exact match test
    print("\n[TEST 1] Sourcing Exact Match: 'sugar'")
    res = normalization_engine.normalize_ingredient("sugar")
    print(f"  Result Name: {res.get('name')}, Processing: {res.get('processing_level')}, Allergy: {res.get('allergy_flags')}")
    assert res.get("name") == "sugar", "Exact match failed for 'sugar'!"
    assert res.get("flagged") is False, "Exact match should NOT be flagged!"

    # 2. E-Number translation test
    print("\n[TEST 2] Translating E-Number: 'E 211'")
    res = normalization_engine.normalize_ingredient("E 211")
    print(f"  Result Name: {res.get('name')}, Processing: {res.get('processing_level')}, Notes: {res.get('safety_notes')[:60]}...")
    assert res.get("name") == "sodium benzoate", "E-Number translation failed for 'E 211'!"
    assert res.get("flagged") is False, "E-Number translation should NOT be flagged!"

    # 3. Synonym mapping test
    print("\n[TEST 3] Sourcing Synonym Mapping: 'high fructose corn syrup'")
    res = normalization_engine.normalize_ingredient("high fructose corn syrup")
    print(f"  Result Name: {res.get('name')}, Additive: {res.get('additive_type')}")
    assert res.get("name") == "corn syrup", "Synonym mapping failed for 'high fructose corn syrup'!"

    # 4. Fuzzy typo correction test
    print("\n[TEST 4] Fuzzy Matching Typo: 'whaet floour'")
    res = normalization_engine.normalize_ingredient("whaet floour")
    print(f"  Result Name: {res.get('name')}, Original Typo: {res.get('original_typo')}")
    assert res.get("name") == "wheat flour", "Fuzzy typo correction failed for 'whaet floour'!"

    # 5. Unknown ingredient fallback and moderation queue logging
    print("\n[TEST 5] Sourcing Unknown Ingredient: 'xylo-oligosaccharide'")
    res = normalization_engine.normalize_ingredient("xylo-oligosaccharide")
    print(f"  Result Name: {res.get('name')}, Flagged: {res.get('flagged')}")
    assert res.get("flagged") is True, "Unknown ingredient should be flagged!"
    
    from app.db.database import SessionLocal
    from app.models.database_models import ModerationQueue
    import json
    
    db = SessionLocal()
    try:
        logged = db.query(ModerationQueue).filter(
            ModerationQueue.item_type == "ingredient",
            ModerationQueue.item_id == "xylo-oligosaccharide"
        ).first()
        print(f"  Queue verification in SQLite Moat: {logged}")
        assert logged is not None, "Unknown ingredient failed to queue in local db moat!"
        data = json.loads(logged.item_data_json)
        assert data.get("count") >= 1, "Count should be tracked!"
    finally:
        db.close()

    print("\n==================================================")
    print("ALL DETERMINISTIC NORMALIZATION ENGINE TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_normalization_tests()
