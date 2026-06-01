import json
from typing import Dict, Any, List
from collections import Counter

def calculate_history_insights(scans: List[Any]) -> Dict[str, Any]:
    """
    Analyzes historical scan records to extract behavioral insights.
    Returns:
    - common_category: Most scanned subcategory.
    - sugar_heavy_count: Count of high sugar load scans.
    - ultra_processed_ratio: % of scans that are NOVA 4.
    - additive_trends: Notable additives appearing in history.
    - swap_suggestions: Recommended alternatives based on scanned items.
    """
    if not scans:
        return {
            "has_scans": False,
            "common_category": "None",
            "sugar_heavy_count": 0,
            "ultra_processed_ratio": 0,
            "additive_trends": ["Start scanning products to see healthy insights!"],
            "swap_suggestions": []
        }
        
    total_scans = len(scans)
    
    subcategories = []
    high_sugar_count = 0
    nova_groups = []
    all_additives = []
    
    # Loop over scans
    for s in scans:
        def get_prop(obj, prop, default=None):
            if isinstance(obj, dict):
                return obj.get(prop, default)
            return getattr(obj, prop, default)
            
        name = get_prop(s, "alternative_name", "")
        # Map subcategory
        sub = "Processed Snacks"
        name_lower = name.lower()
        if "soda" in name_lower or "chaas" in name_lower or "sherbet" in name_lower:
            sub = "Carbonated Drinks"
        elif "makhana" in name_lower or "chips" in name_lower or "wafers" in name_lower:
            sub = "Chips & Crisps"
        elif "cookie" in name_lower or "biscuits" in name_lower or "atta" in name_lower:
            sub = "Biscuits & Cookies"
        elif "noodles" in name_lower or "upma" in name_lower or "poha" in name_lower:
            sub = "Instant Noodles"
            
        subcategories.append(sub)
        
        # Sugar load checking: look at explanation or breakdown
        breakdown = get_prop(s, "breakdown_json", "[]")
        if isinstance(breakdown, str):
            try:
                breakdown_list = json.loads(breakdown)
            except:
                breakdown_list = []
        else:
            breakdown_list = get_prop(s, "breakdown", [])
            
        for item in breakdown_list:
            reason = item.get("reason", "").lower() if isinstance(item, dict) else getattr(item, "reason", "").lower()
            if "sugar" in reason:
                high_sugar_count += 1
            if "color" in reason or "dye" in reason or "tartrazine" in reason:
                all_additives.append("Synthetic Colors")
            if "additive" in reason or "stabilizer" in reason:
                all_additives.append("Food Stabilizers")
                
        grade = get_prop(s, "grade", "")
        if "nova 4" in grade.lower() or get_prop(s, "score", 80) <= 60:
            nova_groups.append(4)
        else:
            nova_groups.append(2)
            
    # Calculate stats
    category_counts = Counter(subcategories)
    common_category = category_counts.most_common(1)[0][0] if subcategories else "Snacks"
    
    nova_4_count = sum(1 for n in nova_groups if n == 4)
    ultra_processed_ratio = int((nova_4_count / total_scans) * 100) if total_scans > 0 else 0
    
    # Formulate non-judgmental additive messages
    trends = []
    if high_sugar_count >= 3:
        trends.append("You scanned 3 or more sugar-sweetened options recently. Standard guidelines suggest checking portion sizes for optimal glycemic control.")
    if all_additives:
        counts = Counter(all_additives)
        most_common_add = counts.most_common(1)[0][0]
        trends.append(f"{most_common_add} were found frequently in your scan history. Bypassing E-number emulsifiers promotes gut microflora health.")
    if ultra_processed_ratio >= 60:
        trends.append("Over 60% of scanned products are ultra-processed (NOVA 4). Swapping just one snack a day with a NOVA 1 culinary staple significantly lowers additive load.")
        
    if not trends:
        trends.append("Excellent scan variety! You are maintaining a highly diverse nutritional balance across categories.")
        
    # Swap suggestions based on common category
    swaps = []
    if common_category == "Carbonated Drinks":
        swaps.append({
            "original": "Commercial Sweetened Sodas",
            "swap": "Fresh Lime Soda or Spiced Chaas",
            "reason": "Eliminates high phosphoric acid loading and insulin surges."
        })
    elif common_category == "Chips & Crisps":
        swaps.append({
            "original": "Deep Fried Potato Chips",
            "swap": "Roasted Ghee Masala Makhana",
            "reason": "Adds +5g of gut-friendly fiber and cuts trans fats completely."
        })
    elif common_category == "Biscuits & Cookies":
        swaps.append({
            "original": "Refined flour (Maida) Tea biscuits",
            "swap": "Homemade Oats & Jaggery Cookies",
            "reason": "Stripped maida flour is replaced with calcium-dense whole grains."
        })
    else:
        swaps.append({
            "original": "Instant Packaged Noodles",
            "swap": "Vegetable Semiya Upma or Millet Noodles",
            "reason": "Lowers extreme sodium seasonings by 75% while boosting fresh greens."
        })
        
    return {
        "has_scans": True,
        "common_category": common_category,
        "sugar_heavy_count": high_sugar_count,
        "ultra_processed_ratio": ultra_processed_ratio,
        "additive_trends": trends,
        "swap_suggestions": swaps
    }
