from nutrition_db import get_fruit_nutrition

fruit_recipes = {
    "BAKED_TREATS": {
        "Classic Apple Pie": {
            "fruits": ["APPLES"],
            "quantities": [500],
            "instructions": "Slice apples, mix with cinnamon and sugar, bake in pie crust until golden brown",
            "calories": 280,
            "preparation_time": "60 minutes",
            "difficulty": "Medium"
        },
        "Mixed Berry Crumble": {
            "fruits": ["BLACKBERRIES", "RASPBERRIES", "BLUEBERRIES"],
            "quantities": [150, 150, 150],
            "instructions": "Mix berries with sugar, top with crumble mixture and bake",
            "calories": 250,
            "preparation_time": "45 minutes",
            "difficulty": "Easy"
        },
        "Citrus Olive Oil Cake": {
            "fruits": ["ORANGES", "LEMONS", "LIMES"],
            "quantities": [100, 50, 50],
            "instructions": "Make cake with olive oil and citrus zest, top with citrus glaze",
            "calories": 260,
            "preparation_time": "55 minutes",
            "difficulty": "Medium"
        }
    },
    "SMOOTHIES": {
        "Cherry Berry Blast": {
            "fruits": ["CHERRIES", "BLUEBERRIES", "RASPBERRIES"],
            "quantities": [150, 50, 50],
            "instructions": "Blend cherries and berries with yogurt and honey",
            "calories": 190,
            "preparation_time": "5 minutes",
            "difficulty": "Easy"
        },
        "Acerola Energy Boost": {
            "fruits": ["ACEROLAS", "ORANGES"],
            "quantities": [100, 150],
            "instructions": "Blend acerolas and oranges with water and honey",
            "calories": 120,
            "preparation_time": "5 minutes",
            "difficulty": "Easy"
        },
        "Tropical Paradise": {
            "fruits": ["MANGOES", "PINEAPPLES", "BANANAS"],
            "quantities": [100, 100, 50],
            "instructions": "Blend fruits with coconut water and honey",
            "calories": 220,
            "preparation_time": "5 minutes",
            "difficulty": "Easy"
        },
        "Berry Blast": {
            "fruits": ["STRAWBERRIES", "BLUEBERRIES", "RASPBERRIES"],
            "quantities": [100, 50, 50],
            "instructions": "Blend all berries with yogurt and ice",
            "calories": 180,
            "preparation_time": "5 minutes",
            "difficulty": "Easy"
        },
        "Citrus Energizer": {
            "fruits": ["ORANGES", "LEMONS", "GRAPEFRUITS"],
            "quantities": [150, 30, 100],
            "instructions": "Blend citrus fruits with water and honey, strain if desired",
            "calories": 120,
            "preparation_time": "7 minutes",
            "difficulty": "Easy"
        },
        "Green Power": {
            "fruits": ["KIWIFRUIT", "APPLES", "GUAVA"],
            "quantities": [100, 150, 100],
            "instructions": "Blend fruits with spinach and coconut water",
            "calories": 160,
            "preparation_time": "5 minutes",
            "difficulty": "Easy"
        }
    },
    "FRUIT_SALADS": {
        "Cherry Pear Delight": {
            "fruits": ["CHERRIES", "PEARS", "GRAPES"],
            "quantities": [100, 150, 100],
            "instructions": "Slice pears, pit cherries, add grapes and drizzle with honey",
            "calories": 210,
            "preparation_time": "15 minutes",
            "difficulty": "Easy"
        },
        "Tropical Acerola Mix": {
            "fruits": ["ACEROLAS", "MANGOES", "PINEAPPLES"],
            "quantities": [100, 150, 150],
            "instructions": "Mix fruits and serve with a lime-honey dressing",
            "calories": 200,
            "preparation_time": "10 minutes",
            "difficulty": "Easy"
        },
        "Mediterranean Mix": {
            "fruits": ["POMEGRANATES", "FIGS", "GRAPES"],
            "quantities": [50, 100, 100],
            "instructions": "Combine fruits and drizzle with honey",
            "calories": 200,
            "preparation_time": "10 minutes",
            "difficulty": "Easy"
        },
        "Summer Delight": {
            "fruits": ["WATERMELONS", "PEACHES", "CANTALOUPES"],
            "quantities": [200, 100, 100],
            "instructions": "Cube fruits and mix with mint leaves",
            "calories": 180,
            "preparation_time": "15 minutes",
            "difficulty": "Easy"
        },
        "Tropical Bowl": {
            "fruits": ["MANGOES", "PINEAPPLES", "COCONUTS"],
            "quantities": [150, 150, 50],
            "instructions": "Dice mangoes and pineapples, top with coconut flakes",
            "calories": 220,
            "preparation_time": "12 minutes",
            "difficulty": "Easy"
        },
        "Berry Medley": {
            "fruits": ["STRAWBERRIES", "BLUEBERRIES", "BLACKBERRIES", "RASPBERRIES"],
            "quantities": [100, 50, 50, 50],
            "instructions": "Mix all berries and serve with a light honey-lime dressing",
            "calories": 150,
            "preparation_time": "8 minutes",
            "difficulty": "Easy"
        }
    },
    "DESSERTS": {
        "Cherry Pear Tart": {
            "fruits": ["CHERRIES", "PEARS"],
            "quantities": [200, 300],
            "instructions": "Arrange sliced pears and pitted cherries on pastry, bake until golden",
            "calories": 290,
            "preparation_time": "45 minutes",
            "difficulty": "Medium"
        },
        "Acerola Ice Pops": {
            "fruits": ["ACEROLAS", "STRAWBERRIES", "RASPBERRIES"],
            "quantities": [100, 100, 100],
            "instructions": "Blend fruits with honey, freeze in popsicle molds",
            "calories": 120,
            "preparation_time": "10 minutes (plus freezing)",
            "difficulty": "Easy"
        },
        "Fruit Tart": {
            "fruits": ["STRAWBERRIES", "KIWIFRUIT", "BLUEBERRIES"],
            "quantities": [100, 50, 50],
            "instructions": "Arrange fruits on pastry cream in a tart shell",
            "calories": 300,
            "preparation_time": "30 minutes",
            "difficulty": "Medium"
        },
        "Tropical Pavlova": {
            "fruits": ["PASSIONFRUIT", "MANGOES", "PINEAPPLES"],
            "quantities": [100, 100, 100],
            "instructions": "Top meringue with whipped cream and fresh fruits",
            "calories": 280,
            "preparation_time": "45 minutes",
            "difficulty": "Medium"
        },
        "Stone Fruit Cobbler": {
            "fruits": ["PEACHES", "PLUMS", "APRICOTS"],
            "quantities": [200, 100, 100],
            "instructions": "Layer fruits with cobbler topping and bake until golden",
            "calories": 320,
            "preparation_time": "50 minutes",
            "difficulty": "Medium"
        }
    },
    "HEALTHY_SNACKS": {
        "Avocado Toast": {
            "fruits": ["AVOCADOS", "POMEGRANATES"],
            "quantities": [100, 30],
            "instructions": "Mash avocado on toast, top with pomegranate seeds",
            "calories": 220,
            "preparation_time": "10 minutes",
            "difficulty": "Easy"
        },
        "Tropical Trail Mix": {
            "fruits": ["COCONUTS", "GUAVA", "MANGOES"],
            "quantities": [50, 50, 50],
            "instructions": "Mix dried fruits with nuts and seeds",
            "calories": 180,
            "preparation_time": "5 minutes",
            "difficulty": "Easy"
        },
        "Mediterranean Platter": {
            "fruits": ["OLIVES", "FIGS", "GRAPES"],
            "quantities": [50, 100, 100],
            "instructions": "Arrange fruits with cheese and nuts",
            "calories": 300,
            "preparation_time": "15 minutes",
            "difficulty": "Easy"
        }
    }
}

def get_recipes_by_fruit(fruit_name):
    """Get all recipes that use a specific fruit."""
    matching_recipes = {}
    for category, recipes in fruit_recipes.items():
        category_matches = {}
        for recipe_name, recipe in recipes.items():
            if fruit_name.upper() in recipe["fruits"]:
                category_matches[recipe_name] = recipe
        if category_matches:
            matching_recipes[category] = category_matches
    return matching_recipes

def calculate_recipe_nutrition(recipe):
    """Calculate total nutrition for a recipe."""
    total_nutrition = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fiber": 0,
        "vitamin_c": 0
    }
    
    for fruit, quantity in zip(recipe["fruits"], recipe["quantities"]):
        fruit_nutrition = get_fruit_nutrition(fruit)
        if fruit_nutrition:
            ratio = quantity / fruit_nutrition["serving_size"]
            for key in total_nutrition:
                if key in fruit_nutrition:
                    total_nutrition[key] += fruit_nutrition[key] * ratio
    
    return total_nutrition
