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
    {"category": "Instant Foods", "subcategory": "Pasta", "snack_type": "Soft", "flavor_profile": "Savory", "texture_profile": "Soft", "craving_profile": "Savory", "convenience_profile": 5, "processing_level": 4}
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
    }
]

def seed_database(db: Session):
    """
    Seeds initial taxonomy categories and curated alternatives if table is empty.
    """
    if db.query(ProductCategory).count() > 0:
        return
        
    print("Database seeding: Populating taxonomy categories...")
    category_map = {}
    for cat in SEED_CATEGORIES:
        db_cat = ProductCategory(
            category_name=cat["category"],
            subcategory_name=cat["subcategory"],
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
        category_map[cat["subcategory"]] = db_cat.id
        
    print("Database seeding: Populating healthy alternatives...")
    for alt in SEED_ALTERNATIVES:
        sub_name = alt["subcategory_name"]
        cat_id = category_map.get(sub_name)
        if cat_id:
            db_alt = Alternative(
                name=alt["name"],
                recipe=alt["recipe"],
                prep_time_mins=alt["prep_time_mins"],
                approx_cost_inr=alt["approx_cost_inr"],
                category_id=cat_id
            )
            db.add(db_alt)
            
    db.commit()
    print("Database seeding completed successfully.")

def migrate_tinydb_to_sqlite():
    """
    Safely executes TinyDB to SQLite migrations at application startup.
    Runs only if there is TinyDB data and SQLite has not yet been populated.
    """
    # Create SQLite tables if they do not exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Seed initial taxonomy
        seed_database(db)
        
        # 2. Check if migration needs to run
        legacy_db_path = "ecosaur_db.json"
        if not os.path.exists(legacy_db_path):
            print("No legacy TinyDB file found. Skipping data migration.")
            return

        # Check if migration was already performed
        if db.query(Scan).count() > 0 or db.query(User).count() > 1:
            print("Relational database already populated. Legacy data migration skipped.")
            return

        print("Migrating legacy data from TinyDB to SQLite...")
        with open(legacy_db_path, "r", encoding="utf-8") as f:
            legacy_data = json.load(f)
            
        # Migrate Users
        legacy_users = legacy_data.get("users", {})
        for user_key, u_val in legacy_users.items():
            u_id = u_val.get("id", "default")
            existing_user = db.query(User).filter(User.id == u_id).first()
            if not existing_user:
                new_user = User(
                    id=u_id,
                    health_mode=u_val.get("health_mode", "General"),
                    created_at=datetime.fromisoformat(u_val.get("created_at")) if u_val.get("created_at") else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(u_val.get("updated_at")) if u_val.get("updated_at") else datetime.utcnow()
                )
                db.add(new_user)
        db.commit()

        # Migrate Scans
        legacy_scans = legacy_data.get("scans", {})
        for scan_key, s_val in legacy_scans.items():
            # Get cached alternative values
            alt_dict = s_val.get("alternative", {})
            breakdown_list = s_val.get("breakdown", [])
            
            # Formulate scan models
            dt = datetime.utcnow()
            if s_val.get("date"):
                try:
                    dt = datetime.fromisoformat(s_val.get("date"))
                except:
                    pass
                    
            new_scan = Scan(
                id=s_val.get("id", str(uuid.uuid4())),
                user_id=s_val.get("user_id", "default"),
                date=dt,
                corrected_text=s_val.get("corrected_text", ""),
                score=s_val.get("score", 80),
                grade=s_val.get("grade", "A"),
                explanation=s_val.get("explanation", ""),
                alternative_name=alt_dict.get("name", ""),
                alternative_recipe=alt_dict.get("recipe", ""),
                alternative_prep_time=alt_dict.get("prep_time_mins", 15),
                alternative_cost=alt_dict.get("approx_cost_inr", 40),
                breakdown_json=json.dumps(breakdown_list),
                confidence_ocr=0.9,
                confidence_match=0.9,
                confidence_analysis=0.9,
                confidence_rec=0.9
            )
            db.add(new_scan)

        # Migrate Unknown Ingredients to Moderation Queue
        legacy_ing = legacy_data.get("unknown_ingredients", {})
        for ing_key, ing_val in legacy_ing.items():
            name = ing_val.get("name", "")
            count = ing_val.get("count", 1)
            
            queue_item = {
                "name": name,
                "count": count,
                "first_scanned": ing_val.get("first_scanned"),
                "last_scanned": ing_val.get("last_scanned")
            }
            
            moderation_entry = ModerationQueue(
                item_type="ingredient",
                item_id=name,
                item_data_json=json.dumps(queue_item),
                status="pending",
                reviewer_notes=f"Migrated from legacy TinyDB count: {count}"
            )
            db.add(moderation_entry)

        db.commit()
        print("Legacy TinyDB data successfully migrated to SQLite ORM.")

        # Rename legacy DB to keep backup
        backup_name = "ecosaur_db_legacy.json.bak"
        try:
            if os.path.exists(backup_name):
                os.remove(backup_name)
            os.rename(legacy_db_path, backup_name)
            print(f"Legacy database archived to: {backup_name}")
        except Exception as err:
            print(f"Warning: Failed to rename legacy TinyDB: {err}")

    except Exception as e:
        db.rollback()
        print(f"Error executing TinyDB SQLite migration: {e}")
    finally:
        db.close()
