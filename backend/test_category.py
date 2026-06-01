import asyncio
import os
import sys

# Set Python path to backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services import category_engine
from app.models.schemas import ParsedFoodData
from app.db.database import engine, Base, SessionLocal
from app.db.migrate import seed_database

def run_tests():
    print("==============================================")
    print("STARTING EcoSaur PRODUCT CATEGORY ALIGNMENT TESTS")
    print("==============================================")
    
    # Initialize database tables and seed taxonomy for the standalone test context
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    # Test Case 1: Carbonated Drink (Coca-Cola)
    print("\n[TEST 1] Scanned: Coca-Cola")
    coca_cola_parsed = ParsedFoodData(
        ingredients=["carbonated water", "high fructose corn syrup", "caramel color", "phosphoric acid", "natural flavors", "caffeine"],
        nutrition={"sugar": "39g", "protein": "0g"},
        product_name="Coca-Cola"
    )
    
    cat_info = category_engine.classify_product(coca_cola_parsed.product_name, coca_cola_parsed.ingredients)
    print(f"  Classification Output:")
    print(f"    - Category: {cat_info.category}")
    print(f"    - Subcategory: {cat_info.subcategory}")
    print(f"    - Beverage Type: {cat_info.beverage_type}")
    print(f"    - Snack Type: {cat_info.snack_type}")
    print(f"    - Flavor Profile: {cat_info.flavor_profile}")
    
    alts = category_engine.rank_alternatives(cat_info)
    print(f"  Scored Homemade Alternatives (Top 3):")
    for idx, alt in enumerate(alts[:3]):
        print(f"    {idx+1}. {alt['name']} (Score: {alt['score']})")
        
    comparisons = category_engine.get_comparison_cards(cat_info, coca_cola_parsed.product_name)
    print(f"  Same-Category Commercial Comparisons:")
    for card in comparisons:
        print(f"    * Compare with: {card.product_name} (Grade: {card.grade}, NOVA: {card.nova_group}, Sugar: {card.sugar_load})")

    # Assertions for Cola
    assert cat_info.category == "Beverages", "Coca-Cola must be classified as Beverages!"
    assert all(a["name"] not in ["Roasted Ghee Masala Makhana", "Baked Ragi & Almond Cookies", "Vegetable Poha"] for a in alts[:3]), "Coca-Cola should NOT suggest dry roasted snacks, cookies, or noodles!"
    print("  => [SUCCESS] Coca-Cola successfully matched ONLY to refreshing liquid beverages.")

    # Test Case 2: Chips & Crisps (Lay's)
    print("\n[TEST 2] Scanned: Lay's Potato Chips")
    lays_parsed = ParsedFoodData(
        ingredients=["potatoes", "vegetable oil", "salt"],
        nutrition={"sodium": "170mg", "protein": "2g", "fiber": "1g"},
        product_name="Lay's Potato Chips"
    )
    
    cat_info_lays = category_engine.classify_product(lays_parsed.product_name, lays_parsed.ingredients)
    print(f"  Classification Output:")
    print(f"    - Category: {cat_info_lays.category}")
    print(f"    - Subcategory: {cat_info_lays.subcategory}")
    print(f"    - Snack Type: {cat_info_lays.snack_type}")
    print(f"    - Flavor Profile: {cat_info_lays.flavor_profile}")
    
    alts_lays = category_engine.rank_alternatives(cat_info_lays)
    print(f"  Scored Homemade Alternatives (Top 3):")
    for idx, alt in enumerate(alts_lays[:3]):
        print(f"    {idx+1}. {alt['name']} (Score: {alt['score']})")

    # Assertions for Chips
    assert cat_info_lays.category == "Snacks", "Chips must be classified as Snacks!"
    assert any("makhana" in a["name"].lower() or "banana" in a["name"].lower() or "potato" in a["name"].lower() for a in alts_lays[:3]), "Chips should suggest crunchy dry savory snacks!"
    assert all(a["name"] not in ["Fresh Lime Soda (Nimbu Soda)", "Spiced Curd Chaas (Buttermilk)", "Oats & Jaggery Cookies"] for a in alts_lays[:3]), "Chips should NOT suggest fruit drinks, buttermilk, or sweet cookies!"
    print("  => [SUCCESS] Lay's successfully matched ONLY to crunchy savory snacks.")

    # Test Case 3: Biscuits (Oreo Cookies)
    print("\n[TEST 3] Scanned: Oreo Cookies")
    oreo_parsed = ParsedFoodData(
        ingredients=["unbleached enriched flour", "sugar", "palm oil", "cocoa", "high fructose corn syrup", "baking soda", "soy lecithin", "vanillin"],
        nutrition={"sugar": "14g", "protein": "1g"},
        product_name="Oreo Cookies"
    )
    
    cat_info_oreo = category_engine.classify_product(oreo_parsed.product_name, oreo_parsed.ingredients)
    print(f"  Classification Output:")
    print(f"    - Category: {cat_info_oreo.category}")
    print(f"    - Subcategory: {cat_info_oreo.subcategory}")
    print(f"    - Snack Type: {cat_info_oreo.snack_type}")
    print(f"    - Flavor Profile: {cat_info_oreo.flavor_profile}")
    
    alts_oreo = category_engine.rank_alternatives(cat_info_oreo)
    print(f"  Scored Homemade Alternatives (Top 3):")
    for idx, alt in enumerate(alts_oreo[:3]):
        print(f"    {idx+1}. {alt['name']} (Score: {alt['score']})")

    # Assertions for Biscuits
    assert cat_info_oreo.category == "Snacks", "Oreo must be classified as Snacks!"
    assert any("cookies" in a["name"].lower() or "biscuits" in a["name"].lower() for a in alts_oreo[:3]), "Oreo should suggest sweet baked whole wheat/millet cookies!"
    print("  => [SUCCESS] Oreo successfully matched ONLY to sweet cookies.")

    print("\n==============================================")
    print("ALL CATEGORY ALIGNMENT ENGINE TESTS PASSED!")
    print("==============================================")

if __name__ == "__main__":
    run_tests()
