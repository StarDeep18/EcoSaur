import os
import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, Base, engine, DB_PATH
from app.models.database_models import User, ProductCategory, Product, Ingredient, Alternative, Scan, ModerationQueue, OCRCorrection

# Curated seed categories with their hierarchical and taxonomic attributes
SEED_CATEGORIES = [
    # Beverages
    {"category": "Beverages", "subcategory": "Carbonated Drinks", "beverage_type": "Fizzy", "flavor_profile": "Sweet", "texture_profile": "Liquid", "craving_profile": "Fizzy", "convenience_profile": 5, "processing_level": 4},
    {"category": "Beverages", "subcategory": "Juices & Nectars", "beverage_type": "Fruit-based", "flavor_profile": "Sweet & Sour", "texture_profile": "Liquid", "craving_profile": "Fruity", "convenience_profile": 5, "processing_level": 4},
    {"category": "Beverages", "subcategory": "Dairy-based", "beverage_type": "Dairy-based", "flavor_profile": "Savory", "texture_profile": "Liquid", "craving_profile": "Creamy", "convenience_profile": 4, "processing_level": 3},
    {"category": "Beverages", "subcategory": "Herbal", "beverage_type": "Herbal", "flavor_profile": "Bitter & Sweet", "texture_profile": "Liquid", "craving_profile": "Herbal", "convenience_profile": 4, "processing_level": 2},
    
    # Snacks
    {"category": "Snacks", "subcategory": "Chips & Crisps", "snack_type": "Crunchy", "flavor_profile": "Salty & Spicy", "texture_profile": "Crunchy", "craving_profile": "Salty", "convenience_profile": 5, "processing_level": 4},
    {"category": "Snacks", "subcategory": "Biscuits & Cookies", "snack_type": "Crunchy", "flavor_profile": "Sweet", "texture_profile": "Crunchy", "craving_profile": "Sweet", "convenience_profile": 5, "processing_level": 4},
    {"category": "Snacks", "subcategory": "Protein Snacks", "snack_type": "Savory", "flavor_profile": "Savory", "texture_profile": "Chewy", "craving_profile": "Savory", "convenience_profile": 5, "processing_level": 3},
    {"category": "Snacks", "subcategory": "Savory Snacks", "snack_type": "Crunchy", "flavor_profile": "Salty & Spicy", "texture_profile": "Crunchy", "craving_profile": "Salty", "convenience_profile": 5, "processing_level": 4},
    {"category": "Snacks", "subcategory": "Chocolates & Sweets", "snack_type": "Sweet", "flavor_profile": "Chocolatey", "texture_profile": "Soft", "craving_profile": "Sweet", "convenience_profile": 5, "processing_level": 4},
    
    # Breakfast
    {"category": "Breakfast", "subcategory": "Cereals", "snack_type": "Crunchy", "flavor_profile": "Sweet", "texture_profile": "Crunchy", "craving_profile": "Sweet", "convenience_profile": 5, "processing_level": 4},
    {"category": "Breakfast", "subcategory": "Instant Breakfast", "snack_type": "Soft", "flavor_profile": "Savory", "texture_profile": "Soft", "craving_profile": "Savory", "convenience_profile": 5, "processing_level": 3},
    {"category": "Breakfast", "subcategory": "Breakfast Bowls", "snack_type": "Soft", "flavor_profile": "Sweet & Nutty", "texture_profile": "Creamy", "craving_profile": "Sweet", "convenience_profile": 4, "processing_level": 2},
    
    # Instant Foods
    {"category": "Instant Foods", "subcategory": "Instant Noodles", "snack_type": "Soft", "flavor_profile": "Salty & Spicy", "texture_profile": "Slurpy", "craving_profile": "Savory", "convenience_profile": 5, "processing_level": 4},
    {"category": "Instant Foods", "subcategory": "Soup Mixes", "snack_type": "Soft", "flavor_profile": "Savory", "texture_profile": "Liquid", "craving_profile": "Savory", "convenience_profile": 5, "processing_level": 4},
    {"category": "Instant Foods", "subcategory": "Pasta", "snack_type": "Soft", "flavor_profile": "Savory", "texture_profile": "Soft", "craving_profile": "Savory", "convenience_profile": 5, "processing_level": 4},

    # Bakery
    {"category": "Bakery", "subcategory": "Bread", "snack_type": "Soft", "beverage_type": "None", "flavor_profile": "Savory", "texture_profile": "Soft", "craving_profile": "Warm", "convenience_profile": 5, "processing_level": 3},
    {"category": "Bakery", "subcategory": "Cakes & Pastries", "snack_type": "Soft", "beverage_type": "None", "flavor_profile": "Sweet", "texture_profile": "Soft", "craving_profile": "Sweet", "convenience_profile": 4, "processing_level": 4},
    {"category": "Bakery", "subcategory": "Rusk & Crackers", "snack_type": "Crunchy", "beverage_type": "None", "flavor_profile": "Savory", "texture_profile": "Crunchy", "craving_profile": "Salty", "convenience_profile": 5, "processing_level": 4},

    # Dairy
    {"category": "Dairy", "subcategory": "Yogurt", "snack_type": "Soft", "beverage_type": "None", "flavor_profile": "Sweet & Sour", "texture_profile": "Creamy", "craving_profile": "Creamy", "convenience_profile": 5, "processing_level": 2},
    {"category": "Dairy", "subcategory": "Cheese", "snack_type": "Soft", "beverage_type": "None", "flavor_profile": "Savory", "texture_profile": "Soft", "craving_profile": "Creamy", "convenience_profile": 4, "processing_level": 3},
    {"category": "Dairy", "subcategory": "Butter & Spreads", "snack_type": "Soft", "beverage_type": "None", "flavor_profile": "Savory", "texture_profile": "Creamy", "craving_profile": "Creamy", "convenience_profile": 5, "processing_level": 3},

    # Condiments
    {"category": "Condiments", "subcategory": "Sauces & Ketchup", "snack_type": "Soft", "beverage_type": "None", "flavor_profile": "Tangy", "texture_profile": "Liquid", "craving_profile": "Tangy", "convenience_profile": 5, "processing_level": 4},
    {"category": "Condiments", "subcategory": "Jams & Spreads", "snack_type": "Soft", "beverage_type": "None", "flavor_profile": "Sweet", "texture_profile": "Sticky", "craving_profile": "Sweet", "convenience_profile": 5, "processing_level": 4},
    {"category": "Condiments", "subcategory": "Salad Dressings", "snack_type": "Soft", "beverage_type": "None", "flavor_profile": "Sour & Sweet", "texture_profile": "Liquid", "craving_profile": "Tangy", "convenience_profile": 5, "processing_level": 4}
]

# Curated seed alternatives
SEED_ALTERNATIVES = [
    {
        "name": "Spiced Curd Chaas (Buttermilk)",
        "subcategory_name": "Carbonated Drinks",
        "prep_time_mins": 3,
        "approx_cost_inr": 15,
        "recipe": "1. Whisk fresh curd (yogurt) with cold water in a 1:2 ratio.\n2. Add finely chopped coriander leaves, a bit of minced green chili, and a pinch of rock salt.\n3. Sprinkle roasted cumin powder (jeera) and mix well.\n4. Serve cold as a gut-healthy, high-protein digestive refreshment."
    },
    {
        "name": "Fresh Lime Soda (Nimbu Soda)",
        "subcategory_name": "Carbonated Drinks",
        "prep_time_mins": 2,
        "approx_cost_inr": 10,
        "recipe": "1. Squeeze half a lime into fresh sparkling carbonated water.\n2. Add a pinch of black salt (kala namak) and roasted cumin powder.\n3. Sweeten with a dash of honey or organic jaggery instead of refined sugar.\n4. Serve chilled over ice cubes for a fizzy, vitamin C-rich natural cooler."
    },
    {
        "name": "Traditional Nannari Sherbet",
        "subcategory_name": "Carbonated Drinks",
        "prep_time_mins": 2,
        "approx_cost_inr": 12,
        "recipe": "1. Mix 2 tablespoons of natural nannari (sarsaparilla) root syrup in chilled water.\n2. Add freshly squeezed lime juice.\n3. Stir well with crushed ice.\n4. Enjoy as a traditional body coolant with no synthetic colors or preservatives."
    },
    {
        "name": "Roasted Ghee Masala Makhana",
        "subcategory_name": "Chips & Crisps",
        "prep_time_mins": 6,
        "approx_cost_inr": 25,
        "recipe": "1. Heat a teaspoon of ghee in a heavy pan and add raw makhana (foxnuts).\n2. Roast on low heat until perfectly crunchy (approx 5-7 mins).\n3. Toss in turmeric, red chili powder, chaat masala, and a pinch of rock salt.\n4. Let cool and store in an airtight container for a high-fiber, low-fat alternative."
    },
    {
        "name": "Baked Masala Banana Chips",
        "subcategory_name": "Chips & Crisps",
        "prep_time_mins": 25,
        "approx_cost_inr": 20,
        "recipe": "1. Thinly slice raw bananas and soak them in salted water with turmeric.\n2. Drain and pat dry completely.\n3. Toss with a light drizzle of cold-pressed coconut oil.\n4. Bake at 180°C for 15-20 mins (or air-fry) until crisp. Dust with ground black pepper."
    },
    {
        "name": "Homemade Air-Fried Potato Wafers",
        "subcategory_name": "Chips & Crisps",
        "prep_time_mins": 20,
        "approx_cost_inr": 15,
        "recipe": "1. Slice potatoes paper-thin using a mandoline and soak in cold water.\n2. Drain, dry completely on a towel, and toss with minimal olive oil and sea salt.\n3. Air-fry at 160°C for 12-15 minutes, shaking occasionally until golden crisp.\n4. Sprinkle with a dash of chaat masala."
    },
    {
        "name": "Homemade Oats & Jaggery Cookies",
        "subcategory_name": "Biscuits & Cookies",
        "prep_time_mins": 20,
        "approx_cost_inr": 30,
        "recipe": "1. Blend rolled oats into a coarse flour.\n2. Mix with whole wheat flour (atta), melted ghee, and powdered jaggery.\n3. Add a splash of milk to bind into a dough, then shape into small cookies.\n4. Bake at 170°C for 12-15 mins. Let cool to get crispy, high-fiber biscuits."
    },
    {
        "name": "Baked Ragi & Almond Cookies",
        "subcategory_name": "Biscuits & Cookies",
        "prep_time_mins": 25,
        "approx_cost_inr": 35,
        "recipe": "1. Roast ragi (finger millet) flour slightly to remove raw taste.\n2. Cream together butter and jaggery until light.\n3. Mix ragi, whole wheat flour, crushed almonds, and cardamom.\n4. Shape and bake at 180°C for 15 mins for a nutrient-dense calcium-rich cookie."
    },
    {
        "name": "Vegetable Poha (Flattened Rice)",
        "subcategory_name": "Instant Noodles",
        "prep_time_mins": 10,
        "approx_cost_inr": 15,
        "recipe": "1. Rinse thick poha (flattened rice) under water and drain.\n2. Heat mustard oil, add mustard seeds, curry leaves, green chilies, and roasted peanuts.\n3. Sauté finely chopped onions, carrots, and green peas with turmeric.\n4. Mix in poha and salt, steam for 2 mins, and garnish with fresh coriander and lemon."
    },
    {
        "name": "Homemade Millet Noodles",
        "subcategory_name": "Instant Noodles",
        "prep_time_mins": 15,
        "approx_cost_inr": 40,
        "recipe": "1. Boil store-bought natural multi-millet noodles in water with a drop of oil.\n2. Drain and set aside.\n3. Sauté cabbage, carrots, bell peppers, and spring onions in sesame oil.\n4. Toss the noodles with homemade low-sodium soy sauce, vinegar, and black pepper."
    },
    {
        "name": "Vegetable Semiya Upma",
        "subcategory_name": "Instant Noodles",
        "prep_time_mins": 12,
        "approx_cost_inr": 15,
        "recipe": "1. Dry roast vermicelli (semiya) until golden brown.\n2. Heat oil, temper with mustard seeds, chana dal, curry leaves, and ginger.\n3. Sauté mixed green vegetables with turmeric.\n4. Add water, bring to boil, add semiya, cover and cook on low heat until dry."
    },
    {
        "name": "Homemade Jowar & Bajra Bhakri",
        "subcategory_name": "Bread",
        "prep_time_mins": 10,
        "approx_cost_inr": 8,
        "recipe": "1. Knead fresh jowar or bajra millet flour with warm water into a soft dough.\n2. Flatten into a round disc on a wet cloth or lightly dusted board.\n3. Transfer to a hot clay tawa and roast both sides, applying a splash of water on top.\n4. Serve hot with a dab of A2 ghee for a high-fiber, gluten-free traditional bread."
    },
    {
        "name": "Ragi Banana Jaggery Muffins",
        "subcategory_name": "Cakes & Pastries",
        "prep_time_mins": 30,
        "approx_cost_inr": 20,
        "recipe": "1. Mash 2 ripe bananas and mix with 1/4 cup cold-pressed oil and 1/2 cup jaggery powder.\n2. Fold in 1 cup ragi (finger millet) flour, a pinch of baking powder, and a dash of cardamom.\n3. Pour into greased muffin cups and bake at 180°C for 20-22 minutes.\n4. Enjoy a nutrient-dense, calcium-rich, and iron-packed dessert."
    },
    {
        "name": "Roasted Baked Oats Khakhra",
        "subcategory_name": "Rusk & Crackers",
        "prep_time_mins": 15,
        "approx_cost_inr": 12,
        "recipe": "1. Mix whole wheat atta, coarse oats flour, dry fenugreek leaves (kasuri methi), and black salt.\n2. Knead with minimal water and roll paper-thin.\n3. Roast on a low-flame tawa, pressing continuously with a wooden press until perfectly crisp.\n4. Ideal tea-time crunchy cracker without palm oils or synthetic rising agents."
    },
    {
        "name": "Sweet Cardamom Shrikhand",
        "subcategory_name": "Yogurt",
        "prep_time_mins": 5,
        "approx_cost_inr": 25,
        "recipe": "1. Tie fresh organic curd in a muslin cloth and hang for 4 hours to drain whey (making chakka).\n2. Whisk the thick hung curd with organic honey or raw jaggery powder.\n3. Add active saffron strands dissolved in warm milk, ground green cardamom, and pistachio slivers.\n4. Chill and enjoy as a probiotic, high-protein dessert."
    },
    {
        "name": "Homemade Fresh Lemon Paneer",
        "subcategory_name": "Cheese",
        "prep_time_mins": 15,
        "approx_cost_inr": 45,
        "recipe": "1. Bring 1 liter of fresh grass-fed whole milk to a rolling boil.\n2. Gradually stir in 2 tablespoons of fresh lemon juice until the whey separates completely.\n3. Strain the curds immediately through a clean cheesecloth and rinse with cold water.\n4. Press under a heavy weight for 15 minutes, slice, and enjoy fresh with a dash of black pepper."
    },
    {
        "name": "Traditional Hand-Churned Makhan",
        "subcategory_name": "Butter & Spreads",
        "prep_time_mins": 10,
        "approx_cost_inr": 30,
        "recipe": "1. Collect fresh milk malai (cream) in a container over a week and ferment with a spoon of curd.\n2. Add ice-cold water and churn using a traditional wooden madhani (whisk) until butter floats.\n3. Separate the butterballs, washing them in cold water to remove residual buttermilk.\n4. Lightly salt with rock salt for fresh, preservative-free yellow butter."
    },
    {
        "name": "Mint Coriander Dhaniya Chutney",
        "subcategory_name": "Sauces & Ketchup",
        "prep_time_mins": 5,
        "approx_cost_inr": 10,
        "recipe": "1. Blend fresh coriander leaves, mint leaves, green chilies, and a small slice of ginger.\n2. Add lemon juice, black salt, a pinch of roasted cumin powder, and a splash of water.\n3. Serve fresh as a gut-healthy, iron-rich, tangy dipping sauce with no synthetic coloring or gums."
    },
    {
        "name": "Spiced Honey Amla Murabba",
        "subcategory_name": "Jams & Spreads",
        "prep_time_mins": 45,
        "approx_cost_inr": 40,
        "recipe": "1. Steam fresh amla (gooseberries) until soft and prick with a fork.\n2. Simmer the steamed amla in organic honey or light jaggery syrup with cardamom and black pepper.\n3. Cook until the syrup thickens to a single-thread consistency.\n4. Cool and store for a Vitamin C-rich, immune-boosting sweet spread."
    },
    {
        "name": "Creamy Herb Curd Dressing",
        "subcategory_name": "Salad Dressings",
        "prep_time_mins": 3,
        "approx_cost_inr": 12,
        "recipe": "1. Whisk fresh hung curd with lemon juice, crushed garlic, and black pepper.\n2. Stir in finely chopped fresh dill, mint, coriander, and a drizzle of cold-pressed olive oil.\n3. Drizzle over fresh green salads as a high-protein, zero-stabilizer dressing swap."
  }
]

def seed_database(db: Session):
    """
    Seeds missing taxonomy categories and missing curated alternatives dynamically.
    """
    print("Database seeding: Syncing taxonomy categories...")
    category_map = {}
    
    # Pre-populate category map with existing entries
    existing_cats = db.query(ProductCategory).all()
    for ec in existing_cats:
        category_map[ec.subcategory_name] = ec.id
        
    for cat in SEED_CATEGORIES:
        sub_name = cat["subcategory"]
        if sub_name not in category_map:
            db_cat = ProductCategory(
                category_name=cat["category"],
                subcategory_name=sub_name,
                snack_type=cat.get("snack_type", "None"),
                beverage_type=cat.get("beverage_type", "None"),
                flavor_profile=cat.get("flavor_profile", "Standard"),
                texture_profile=cat.get("texture_profile", "Standard"),
                craving_profile=cat.get("craving_profile", "Standard"),
                convenience_profile=cat.get("convenience_profile", 5),
                processing_level=cat.get("processing_level", 4)
            )
            db.add(db_cat)
            db.flush() # populate ID
            category_map[sub_name] = db_cat.id
            
    print("Database seeding: Syncing healthy alternatives...")
    for alt in SEED_ALTERNATIVES:
        sub_name = alt["subcategory_name"]
        cat_id = category_map.get(sub_name)
        if cat_id:
            # Check if this alternative already exists by name
            existing_alt = db.query(Alternative).filter(
                Alternative.name == alt["name"],
                Alternative.category_id == cat_id
            ).first()
            if not existing_alt:
                db_alt = Alternative(
                    name=alt["name"],
                    recipe=alt["recipe"],
                    prep_time_mins=alt["prep_time_mins"],
                    approx_cost_inr=alt["approx_cost_inr"],
                    category_id=cat_id
                )
                db.add(db_alt)
                
    db.commit()
    print("Database seeding and taxonomy sync completed successfully.")

def init_db():
    """
    Initializes the SQLite database tables and seeds the taxonomy categories
    and healthy alternatives.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        print(f"Error during database initialization: {e}")
    finally:
        db.close()
