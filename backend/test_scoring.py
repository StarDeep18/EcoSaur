import os
import sys

# Set Python path to backend root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services import scoring_service
from src.models.schemas import ParsedFoodData

def run_scoring_tests():
    print("==================================================")
    print("STARTING EcoSaur DETERMINISTIC SCORING UNIT TESTS")
    print("==================================================")

    # TEST CASE 1: Base Case (No additives, moderate sugar, no trans fat)
    # Expected: Base 100 - 5 (moderate sugar) = 95 (Grade S)
    print("\n[TEST 1] Standard general food (moderate sugar, standard protein/fiber)")
    data1 = ParsedFoodData(
        ingredients=["wheat flour", "sugar", "salt"],
        nutrition={"sugar": "8g", "protein": "2g", "fiber": "1g"},
        product_name="biscuit"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data1, "General")
    print(f"  Score: {exp['score']}, Grade: {exp['grade']}, Negatives: {exp['negatives']}")
    assert exp["score"] == 95, f"Expected score 95, got {exp['score']}"
    assert exp["grade"] == "S", f"Expected grade S, got {exp['grade']}"

    # TEST CASE 2: High Sugar + Trans Fat
    # Expected: Base 100 - 15 (high sugar) - 30 (trans fat) = 55 (Grade D)
    print("\n[TEST 2] High sugar + trans fat/hydrogenated oil")
    data2 = ParsedFoodData(
        ingredients=["refined flour", "sugar", "hydrogenated vegetable oil", "salt"],
        nutrition={"sugar": "20g", "protein": "1g", "fiber": "0.5g"},
        product_name="cookie"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data2, "General")
    print(f"  Score: {exp['score']}, Grade: {exp['grade']}, Negatives: {exp['negatives']}")
    assert exp["score"] == 55, f"Expected score 55, got {exp['score']}"
    assert exp["grade"] == "D", f"Expected grade D, got {exp['grade']}"

    # TEST CASE 3: High Protein + High Fiber Boost
    # Expected: Base 100 - 5 (moderate sugar) + 10 (protein) + 10 (fiber) = 100 (Capped at 100, Grade S)
    print("\n[TEST 3] High protein + high fiber boost")
    data3 = ParsedFoodData(
        ingredients=["whole wheat flour", "whey protein isolate", "sugar", "salt"],
        nutrition={"sugar": "6g", "protein": "8g", "fiber": "4g"},
        product_name="protein bar"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data3, "General")
    print(f"  Score: {exp['score']}, Grade: {exp['grade']}, Positives: {exp['positives']}")
    assert exp["score"] == 100, f"Expected score 100, got {exp['score']}"
    assert exp["grade"] == "S", f"Expected grade S, got {exp['grade']}"

    # TEST CASE 4: Personalization modes (Diabetic Friendly)
    # Expected: Triggers diabetic friendly adjustment warnings for sugar
    print("\n[TEST 4] Diabetic Friendly health mode preference check")
    data4 = ParsedFoodData(
        ingredients=["refined flour", "sugar", "salt"],
        nutrition={"sugar": "16g"},
        product_name="cookie"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data4, "Diabetic Friendly")
    print(f"  Diabetic Adjustment: {adj.reason if adj else 'None'}")
    assert adj is not None, "Diabetic friendly adjustment should be active!"
    assert "Diabetic Caution" in adj.reason, "Expected Diabetic Caution warning"

    # TEST CASE 5: Personalization modes (Vegan/Vegetarian)
    # Expected: Vegan fails with gelatin
    print("\n[TEST 5] Vegan health mode preference matching check")
    data5 = ParsedFoodData(
        ingredients=["sugar", "gelatin", "citric acid"],
        nutrition={"sugar": "10g"},
        product_name="gummy candy"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data5, "Vegan")
    print(f"  Vegan Adjustment: {adj.reason if adj else 'None'}")
    assert adj is not None, "Vegan adjustment should be active!"
    assert "Failed vegan criteria" in adj.reason, "Expected Failed vegan criteria warning"

    print("\n==================================================")
    print("ALL EcoSaur DETERMINISTIC SCORING TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_scoring_tests()
