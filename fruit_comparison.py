from nutrition_db import get_fruit_nutrition

def correct_fruit_spelling(fruit_name):
    """Correct common spelling mistakes in fruit names."""
    corrections = {
        'BACKBERRIES': 'BLACKBERRIES',
        'CANALOUPES': 'CANTALOUPES',
        'GAPES': 'GRAPES'
    }
    return corrections.get(fruit_name, fruit_name)

def compare_fruits(fruit_names, serving_size=100):
    """Compare nutritional values of multiple fruits."""
    comparison = {}
    
    for fruit in fruit_names:
        corrected_fruit = correct_fruit_spelling(fruit)
        nutrition = get_fruit_nutrition(corrected_fruit)
        if nutrition:
            # Adjust values based on serving size
            ratio = serving_size / nutrition["serving_size"]
            comparison[fruit] = {
                "calories": nutrition["calories"] * ratio,
                "protein": nutrition["protein"] * ratio,
                "carbs": nutrition["carbs"] * ratio,
                "fiber": nutrition["fiber"] * ratio,
                "vitamin_c": nutrition["vitamin_c"] * ratio,
                "benefits": nutrition["benefits"],
                "season": nutrition["season"]
            }
    
    return comparison

def find_alternatives(fruit_name, criteria="calories", limit=5):
    """Find alternative fruits based on nutritional criteria."""
    from nutrition_db import fruit_nutrition_data
    
    corrected_fruit = correct_fruit_spelling(fruit_name)
    target_fruit = get_fruit_nutrition(corrected_fruit)
    if not target_fruit:
        return []
    
    alternatives = []
    target_value = target_fruit[criteria]
    
    for name, data in fruit_nutrition_data.items():
        if name != fruit_name:
            diff = abs(data[criteria] - target_value)
            alternatives.append({
                "name": name,
                "difference": diff,
                "value": data[criteria],
                "season": data["season"]
            })
    
    # Sort by smallest difference and return top matches
    alternatives.sort(key=lambda x: x["difference"])
    return alternatives[:limit]

def get_nutritional_ranking(criteria="calories", order="asc", limit=10):
    """Rank fruits based on specific nutritional criteria."""
    from nutrition_db import fruit_nutrition_data
    
    ranked_fruits = [
        {
            "name": name,
            "value": data[criteria],
            "serving_size": data["serving_size"],
            "benefits": data["benefits"]
        }
        for name, data in fruit_nutrition_data.items()
    ]
    
    ranked_fruits.sort(key=lambda x: x["value"], 
                      reverse=(order.lower() == "desc"))
    
    return ranked_fruits[:limit]

def get_seasonal_alternatives(fruit_name):
    """Find seasonal alternatives for a fruit."""
    from datetime import datetime
    from nutrition_db import get_current_season
    
    current_season = get_current_season()
    fruit_data = get_fruit_nutrition(fruit_name)
    
    if not fruit_data:
        return []
    
    # If the fruit is in season, suggest complementary fruits
    if current_season.lower() in fruit_data["season"].lower():
        return find_alternatives(fruit_name, "vitamin_c", 3)
    
    # If the fruit is not in season, find similar fruits that are in season
    alternatives = []
    for name, data in fruit_nutrition_data.items():
        if (name != fruit_name and 
            current_season.lower() in data["season"].lower() and
            abs(data["calories"] - fruit_data["calories"]) <= 20):
            alternatives.append({
                "name": name,
                "calories": data["calories"],
                "benefits": data["benefits"]
            })
    
    return alternatives[:5]

def get_complementary_fruits(fruit_name, goal="balanced"):
    """Find fruits that complement the given fruit nutritionally."""
    fruit_data = get_fruit_nutrition(fruit_name)
    if not fruit_data:
        return []
    
    complementary = []
    
    if goal == "balanced":
        # If low in vitamin C, suggest high vitamin C fruits
        if fruit_data["vitamin_c"] < 30:
            vitamin_c_rich = get_nutritional_ranking("vitamin_c", "desc", 3)
            complementary.extend([{
                "name": f["name"],
                "reason": "High in Vitamin C",
                "value": f["value"]
            } for f in vitamin_c_rich])
        
        # If low in fiber, suggest high fiber fruits
        if fruit_data["fiber"] < 2:
            fiber_rich = get_nutritional_ranking("fiber", "desc", 3)
            complementary.extend([{
                "name": f["name"],
                "reason": "High in Fiber",
                "value": f["value"]
            } for f in fiber_rich])
    
    elif goal == "weight_loss":
        # Suggest low-calorie, high-fiber fruits
        low_cal = get_nutritional_ranking("calories", "asc", 5)
        complementary.extend([{
            "name": f["name"],
            "reason": "Low Calorie Option",
            "value": f["value"]
        } for f in low_cal])
    
    return complementary[:5]
