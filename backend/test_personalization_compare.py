import asyncio
import os
import sys

# Set Python path to backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services import scoring, parser
from app.models.schemas import ParsedFoodData

def run_personalization_test():
    print("==================================================")
    print("TESTING PERSONALIZED SCORING ENGINE")
    print("==================================================")
    
    # 1. Sugary Snack (Digestive Biscuit style)
    raw_text = "Ingredients: Wheat Flour, Sugar, Palm Oil, Salt, Sunset Yellow E110, Preservative E211"
    parsed_data = ParsedFoodData(
        ingredients=["wheat flour", "sugar", "palm oil", "salt", "sunset yellow", "preservative e211"],
        nutrition={"protein": "2g", "fiber": "1g", "sugar": "15g"},
        product_name="Biscuit"
    )
    
    print(f"Product: {parsed_data.product_name}")
    print(f"Ingredients: {parsed_data.ingredients}\n")
    
    # Modes to test
    modes = ["General", "Diabetic Friendly", "Child Friendly", "Gym/Fitness", "Vegetarian", "Vegan"]
    
    for mode in modes:
        score, grade, breakdown, adj, details = scoring.calculate_score(parsed_data, health_mode=mode)
        print(f"[{mode} Mode]")
        print(f"  -> Score: {score}/100 | Grade: {grade}")
        if adj:
            print(f"  -> Adjustment: {adj.reason} (Impact: {adj.score_impact})")
        print("  -> Top Breakdown Factors:")
        for factor in breakdown[:2]:
            print(f"     * {factor.reason}: {factor.impact}")
        print("-" * 40)

def run_vegetarian_vegan_violation_test():
    print("\n==================================================")
    print("TESTING VEGETARIAN/VEGAN CRITICAL VIOLATIONS")
    print("==================================================")
    
    # Snack containing gelatin (non-vegetarian) and milk solids (non-vegan)
    parsed_data = ParsedFoodData(
        ingredients=["sugar", "gelatin", "milk solids", "artificial flavor"],
        nutrition={"protein": "3g", "sugar": "25g"},
        product_name="Gummy Bear Milk Candies"
    )
    
    print(f"Product: {parsed_data.product_name}")
    print(f"Ingredients: {parsed_data.ingredients}\n")
    
    # Vegetarian Test
    score, grade, breakdown, adj, _ = scoring.calculate_score(parsed_data, health_mode="Vegetarian")
    print("[Vegetarian Mode]")
    print(f"  -> Score: {score}/100 | Grade: {grade}")
    print(f"  -> Breakdown: {[b.reason for b in breakdown if b.impact == -100]}")
    
    print("-" * 40)
    
    # Vegan Test
    score, grade, breakdown, adj, _ = scoring.calculate_score(parsed_data, health_mode="Vegan")
    print("[Vegan Mode]")
    print(f"  -> Score: {score}/100 | Grade: {grade}")
    print(f"  -> Breakdown: {[b.reason for b in breakdown if b.impact == -100]}")

if __name__ == "__main__":
    run_personalization_test()
    run_vegetarian_vegan_violation_test()
