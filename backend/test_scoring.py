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

    # TEST CASE 1: Base Case (No additives, moderate sugar, no trans fat, moderate sodium from salt)
    # Expected: Base 100 - 5 (moderate sugar) - 5 (moderate sodium) = 90 (Grade S)
    print("\n[TEST 1] Standard general food (moderate sugar, moderate sodium)")
    data1 = ParsedFoodData(
        ingredients=["wheat flour", "sugar", "salt"],
        nutrition={"sugar": "8g", "protein": "2g", "fiber": "1g"},
        product_name="biscuit"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data1, "General")
    print(f"  Score: {exp['score']}, Grade: {exp['grade']}, Negatives: {exp['negatives']}")
    assert exp["score"] == 90, f"Expected score 90, got {exp['score']}"
    assert exp["grade"] == "S", f"Expected grade S, got {exp['grade']}"

    # TEST CASE 2: High Sugar + Trans Fat + Moderate Sodium (from salt)
    # Expected: Base 100 - 15 (high sugar) - 30 (trans fat) - 5 (moderate sodium) = 50 (Grade D)
    print("\n[TEST 2] High sugar + trans fat/hydrogenated oil")
    data2 = ParsedFoodData(
        ingredients=["refined flour", "sugar", "hydrogenated vegetable oil", "salt"],
        nutrition={"sugar": "20g", "protein": "1g", "fiber": "0.5g"},
        product_name="cookie"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data2, "General")
    print(f"  Score: {exp['score']}, Grade: {exp['grade']}, Negatives: {exp['negatives']}")
    assert exp["score"] == 50, f"Expected score 50, got {exp['score']}"
    assert exp["grade"] == "D", f"Expected grade D, got {exp['grade']}"

    # TEST CASE 3: High Protein + High Fiber Boost + Whole Ingredients Bonus
    # Expected: Base 100 - 5 (moderate sugar) - 5 (moderate sodium) + 10 (protein) + 10 (fiber) + 10 (whole grains) = 100 (Capped at 100, Grade S)
    print("\n[TEST 3] High protein + high fiber boost + whole ingredients")
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

    # TEST CASE 6: Palm Oil Deduction
    # Expected: 100 - 5 (moderate sugar) - 10 (palm oil) = 85 (Grade A)
    print("\n[TEST 6] Palm Oil separate deduction check (-10)")
    data6 = ParsedFoodData(
        ingredients=["wheat flour", "palm oil", "sugar"],
        nutrition={"sugar": "6g"},
        product_name="biscuit"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data6, "General")
    print(f"  Score: {exp['score']}, Negatives: {exp['negatives']}")
    assert exp["score"] == 85, f"Expected score 85, got {exp['score']}"

    # TEST CASE 7: High Sodium Deduction
    # Expected: 100 - 15 (high sodium) = 85
    print("\n[TEST 7] High Sodium deduction check (-15)")
    data7 = ParsedFoodData(
        ingredients=["potatoes", "vegetable oil", "salt"],
        nutrition={"sodium": "450mg"},
        product_name="chips"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data7, "General")
    print(f"  Score: {exp['score']}, Negatives: {exp['negatives']}")
    assert exp["score"] == 85, f"Expected score 85, got {exp['score']}"

    # TEST CASE 8: Single & Multiple Preservatives
    # Expected single: 100 - 5 (preservative) = 95
    # Expected multiple: 100 - 10 (multiple preservatives) = 90
    print("\n[TEST 8] Single and Multiple Preservatives check (-5, -10)")
    data8_single = ParsedFoodData(
        ingredients=["water", "sodium benzoate"],
        nutrition={},
        product_name="juice"
    )
    scorecard, breakdown, adj, details, exp_single = scoring_service.calculate_score(data8_single, "General")
    print(f"  Single Preservative Score: {exp_single['score']}, Negatives: {exp_single['negatives']}")
    assert exp_single["score"] == 95, f"Expected score 95, got {exp_single['score']}"

    data8_multi = ParsedFoodData(
        ingredients=["water", "sodium benzoate", "potassium sorbate"],
        nutrition={},
        product_name="juice"
    )
    scorecard, breakdown, adj, details, exp_multi = scoring_service.calculate_score(data8_multi, "General")
    print(f"  Multiple Preservatives Score: {exp_multi['score']}, Negatives: {exp_multi['negatives']}")
    assert exp_multi["score"] == 90, f"Expected score 90, got {exp_multi['score']}"

    # TEST CASE 9: Artificial Colors
    # Expected: 100 - 10 (two colors: sunset yellow, tartrazine) = 90
    print("\n[TEST 9] Artificial Colors deduction check (-5 each)")
    data9 = ParsedFoodData(
        ingredients=["sugar", "sunset yellow", "tartrazine"],
        nutrition={},
        product_name="candy"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data9, "General")
    print(f"  Score: {exp['score']}, Negatives: {exp['negatives']}")
    assert exp["score"] == 85, f"Expected score 85, got {exp['score']}"

    # TEST CASE 10: Long Ingredient List Penalty
    # Expected: 100 - 5 (long list) = 95
    print("\n[TEST 10] Long Ingredient List (>15) check (-5)")
    data10 = ParsedFoodData(
        ingredients=[f"ing_{i}" for i in range(18)],
        nutrition={},
        product_name="complex food"
    )
    scorecard, breakdown, adj, details, exp = scoring_service.calculate_score(data10, "General")
    print(f"  Score: {exp['score']}, Negatives: {exp['negatives']}")
    assert exp["score"] == 95, f"Expected score 95, got {exp['score']}"

    print("\n==================================================")
    print("ALL EcoSaur DETERMINISTIC SCORING TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_scoring_tests()
