import os
import sys

# Set Python path to backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services import scoring
from app.models.schemas import ParsedFoodData

def run_personalization_scorecard_test():
    print("==================================================")
    print("TESTING STARTUP MULTI-DIMENSIONAL SCORECARD ENGINE")
    print("==================================================")
    
    # 1. Sugary Biscuit style snack with common spelling typos
    # Typo check: "whaet floour" -> "wheat flour", "suger" -> "sugar", "plam oyl" -> "palm oil", "potasium sorbate" -> "potassium sorbate"
    raw_ingredients = ["whaet floour", "raw suger", "plam oyl", "salt", "sunset yellow", "potasium sorbate"]
    
    parsed_data = ParsedFoodData(
        ingredients=raw_ingredients,
        nutrition={"protein": "2g", "fiber": "1g", "sugar": "15g"},
        product_name="Biscuit"
    )
    
    print(f"Original Raw Scanned Ingredients: {raw_ingredients}")
    
    # Verify fuzzy normalizer on individual items
    normalized = [scoring.normalize_ingredient_name(ing) for ing in raw_ingredients]
    print(f"Fuzzy Normalized Ingredients: {normalized}\n")
    
    # Modes to test
    modes = ["General", "Diabetic Friendly", "Child Friendly", "Vegetarian", "Vegan"]
    
    for mode in modes:
        scorecard, breakdown, adj, details = scoring.calculate_score(parsed_data, health_mode=mode)
        print(f"[{mode} Mode]")
        print(f"  -> NOVA Processing Group: {scorecard.nova_group} (1=Unprocessed, 4=Ultra-Processed)")
        print(f"  -> Additive Density: {scorecard.additive_density} | Sugar Load: {scorecard.sugar_load} | Sodium Load: {scorecard.sodium_load}")
        print(f"  -> Transparency Index: {scorecard.transparency_index} | Protein: {scorecard.protein_quality} | Fiber: {scorecard.fiber_quality}")
        if adj:
            print(f"  -> Personalized Alert: {adj.reason}")
        print("  -> Top Scientific Breakdowns:")
        for factor in breakdown[:2]:
            print(f"     * {factor.reason}")
        print("-" * 40)

if __name__ == "__main__":
    run_personalization_scorecard_test()
