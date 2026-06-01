from typing import Dict, Any, List

def generate_recommendation_reasoning(
    scanned_info: Any, 
    alternative: Any, 
    scorecard: Any, 
    breakdown: List[Any]
) -> Dict[str, Any]:
    """
    Analyzes the differences between the scanned product and recommended alternative,
    explaining WHY the alternative was chosen in terms of flavor similarity,
    texture profile, convenience matching, processing reduction, and nutritional gains.
    """
    # 1. Deduce category and names
    scanned_cat = getattr(scanned_info, "category", "Snacks")
    scanned_sub = getattr(scanned_info, "subcategory", "Chips & Crisps")
    scanned_flavor = getattr(scanned_info, "flavor_profile", "Standard")
    scanned_nova = getattr(scorecard, "nova_group", 4)
    
    alt_name = getattr(alternative, "name", "Homemade alternative")
    alt_prep = getattr(alternative, "prep_time_mins", 15) or 15
    alt_cost = getattr(alternative, "approx_cost_inr", 40) or 40
    
    # 2. Determine processing drop
    # Seed alternatives are NOVA 1 or 2. Scanned packaged items are typically NOVA 4
    alt_nova = 1 if "fresh" in alt_name.lower() or "lime" in alt_name.lower() or "chaas" in alt_name.lower() else 2
    nova_drop = max(0, scanned_nova - alt_nova)
    
    # 3. Formulate similarity explanations
    flavor_craving_similarity = f"Preserves your preferred {scanned_flavor.lower()} taste profile in a wholesome homemade format."
    
    if "chips" in alt_name.lower() or "makhana" in alt_name.lower():
        texture_similarity = "Crisp and crunchy texture satisfying standard snacking cravings."
    elif "noodles" in alt_name.lower() or "poha" in alt_name.lower() or "upma" in alt_name.lower():
        texture_similarity = "Warm, soft, and slurpy culinary comfort equivalent."
    elif "cookie" in alt_name.lower() or "biscuit" in alt_name.lower():
        texture_similarity = "Crunchy, baked cookie bite ideal for tea-time."
    else:
        texture_similarity = "Refreshing liquid cold beverage."
        
    similarity_explanation = f"Direct equivalent matching your craving for a {scanned_sub.lower()}. {texture_similarity}"
    
    # 4. Formulate nutritional improvements
    nutritional_improvement = "Reduces dietary sodium and chemical loading. Prepared with cold-pressed fats or whole grains."
    sugar_improvement = ""
    sodium_improvement = ""
    additive_improvement = ""
    
    # Build list of matching reason bullet points
    bullets = []
    
    # Direct checks
    is_beverage = (scanned_cat == "Beverages" or getattr(scanned_info, "beverage_type", "None") != "None")
    
    if is_beverage:
        bullets.append("✓ Direct fizzy or liquid refreshment swap")
    else:
        bullets.append(f"✓ Direct category match for {scanned_sub}")
        
    if scanned_nova == 4:
        bullets.append(f"✓ Reduces processing from NOVA 4 (Ultra-Processed) to NOVA {alt_nova}")
        processing_reduction = f"Drastically cuts out industrial refining steps, dropping processing level from Group 4 down to Group {alt_nova}."
    else:
        bullets.append(f"✓ Less industrial processing (NOVA {alt_nova})")
        processing_reduction = "Uses kitchen-stable ingredients rather than factory-locked components."
        
    if getattr(scorecard, "sugar_load", "Low") == "High":
        bullets.append("✓ Dramatically lowers added glycemic sweeteners")
        sugar_improvement = "Replaces highly refined white sugars or high-fructose corn syrups with organic local options like jaggery/honey or eliminates sweetener entirely."
    
    if getattr(scorecard, "sodium_load", "Low") == "High":
        bullets.append("✓ Significantly reduces blood-pressure sodium load")
        sodium_improvement = "Keeps essential mineral salts restricted to kitchen-sprinkled levels rather than industrial preservative bounds."
        
    if getattr(scorecard, "additive_density", "Low") in ["High", "Medium"]:
        bullets.append("✓ Eliminates synthetic E-number colors & stabilizers")
        additive_improvement = "Completely free of artificial colors (e.g. Tartrazine), chemical preservatives, or flavor enhancers (MSG)."
        
    # Standard improvements
    if sugar_improvement or sodium_improvement or additive_improvement:
        nutritional_improvement = " ".join(filter(None, [sugar_improvement, sodium_improvement, additive_improvement]))
    else:
        nutritional_improvement = "Uses natural grains or fresh dairy, offering stable dietary fibers and mineral salts."
        
    # Convenience similarity
    convenience_str = f"Simple kitchen preparation under {alt_prep} minutes"
    bullets.append(f"✓ Fast preparation (Ready in ~{alt_prep} mins)")
    bullets.append(f"✓ Pocket friendly (Est. ₹{alt_cost} cost)")
    
    why_selected = f"Recommended because it matches your preferred flavor and texture profile while replacing refined carbohydrates and synthetic E-number stabilizers with pure, nutrient-dense whole foods."
    
    return {
        "why_selected": why_selected,
        "similarity_explanation": similarity_explanation,
        "nutritional_improvement": nutritional_improvement,
        "processing_reduction": processing_reduction,
        "flavor_craving_similarity": flavor_craving_similarity,
        "bullets": bullets
    }
