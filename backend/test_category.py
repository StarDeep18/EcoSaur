import asyncio
import os
import sys

# Set Python path to backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services import parser, ai_service
from app.models.schemas import ParsedFoodData

async def test_biscuit_category():
    print("--- TEST 1: User explicitly enters Biscuit ---")
    corrected_text = "Ingredients: Wheat Flour, Sugar, Palm Oil, Artificial Color, Raising Agent"
    
    # 1. Parse text with user-provided category "biscuit"
    parsed_data = parser.parse_text(corrected_text, user_product_name="biscuit")
    print(f"Parsed ingredients: {parsed_data.ingredients}")
    print(f"Product name (category): {parsed_data.product_name}")
    
    # 2. Get alternative
    alternative = await ai_service.suggest_alternative(parsed_data)
    print(f"Suggested Alternative Name: {alternative.name}")
    print(f"Recipe:\n{alternative.recipe}\n")
    
    # Verify name contains something related to biscuit/cookie
    name_lower = alternative.name.lower()
    is_valid = "biscuit" in name_lower or "cookie" in name_lower or "rusk" in name_lower
    print(f"Is related to biscuits? {'[YES] MATCHED' if is_valid else '[NO] MISMATCHED'}")

async def test_chips_deduction():
    print("\n--- TEST 2: AI auto-deduces Chips category ---")
    corrected_text = "Ingredients: Dried Potatoes, Vegetable Oil (Cottonseed or Corn Oil), Corn Starch, Rice Flour, Salt"
    
    # 1. Parse text with NO user-provided category
    parsed_data = parser.parse_text(corrected_text, user_product_name=None)
    print(f"Parsed ingredients: {parsed_data.ingredients}")
    print(f"Product name (auto-deduced category): {parsed_data.product_name}")
    
    # 2. Get alternative
    alternative = await ai_service.suggest_alternative(parsed_data)
    print(f"Suggested Alternative Name: {alternative.name}")
    print(f"Recipe:\n{alternative.recipe}\n")
    
    # Verify name contains something related to chips/wedges/makhanas/snack
    name_lower = alternative.name.lower()
    is_valid = any(kw in name_lower for kw in ["chip", "wedge", "makhana", "crisp", "nacho", "fries"])
    print(f"Is related to chips? {'[YES] MATCHED' if is_valid else '[NO] MISMATCHED'}")

if __name__ == "__main__":
    asyncio.run(test_biscuit_category())
    asyncio.run(test_chips_deduction())
