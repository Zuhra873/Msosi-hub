#!/usr/bin/env python3
"""
MsosiHub Sample Data Generator
Run this script to populate the database with sample restaurants and healthy dishes
"""

from app import app, db, User, Restaurant, Dish
from werkzeug.security import generate_password_hash

def create_sample_data():
    with app.app_context():
        print("🌱 Creating MsosiHub sample data...")
        
        # Sample restaurants data
        restaurants_data = [
            {
                "username": "healthy_bites",
                "restaurant_name": "Healthy Bites Tanzania",
                "description": "Fresh, organic, and locally sourced healthy meals for the modern Tanzanian",
                "address": "Masaki, Dar es Salaam",
                "phone": "+255 754 123 001",
                "dishes": [
                    {"title": "Quinoa Power Bowl", "description": "Quinoa with roasted vegetables, avocado, and tahini dressing", "price": 15000, "category": "Bowls"},
                    {"title": "Grilled Tilapia with Sweet Potato", "description": "Fresh tilapia grilled with herbs, served with roasted sweet potato", "price": 18000, "category": "Main Course"},
                    {"title": "Green Smoothie", "description": "Spinach, mango, banana, and coconut water blend", "price": 8000, "category": "Beverages"},
                    {"title": "Lentil Curry", "description": "Protein-rich lentils in coconut curry sauce", "price": 12000, "category": "Curry"},
                    {"title": "Fresh Fruit Salad", "description": "Seasonal tropical fruits with lime dressing", "price": 7000, "category": "Desserts"},
                ]
            },
            {
                "username": "mama_vitamu",
                "restaurant_name": "Mama Vitamu Kitchen",
                "description": "Traditional Tanzanian dishes made healthy with modern cooking techniques",
                "address": "Mikocheni, Dar es Salaam",
                "phone": "+255 754 123 002",
                "dishes": [
                    {"title": "Whole Grain Ugali with Sukuma Wiki", "description": "Nutritious whole grain ugali with organic sukuma wiki", "price": 8000, "category": "Traditional"},
                    {"title": "Grilled Chicken Breast", "description": "Lean grilled chicken with African spices", "price": 16000, "category": "Protein"},
                    {"title": "Brown Rice Pilau", "description": "Healthy brown rice pilau with vegetables", "price": 12000, "category": "Rice"},
                    {"title": "Baobab Juice", "description": "Natural baobab fruit juice, rich in vitamin C", "price": 6000, "category": "Beverages"},
                    {"title": "Baked Sweet Potato", "description": "Oven-baked sweet potato with herbs", "price": 5000, "category": "Sides"},
                ]
            },
            {
                "username": "ocean_fresh",
                "restaurant_name": "Ocean Fresh Seafood",
                "description": "Fresh seafood from the Indian Ocean, prepared with health-conscious methods",
                "address": "Msasani Peninsula, Dar es Salaam",
                "phone": "+255 754 123 003",
                "dishes": [
                    {"title": "Grilled Salmon", "description": "Fresh salmon grilled with lemon and herbs", "price": 25000, "category": "Seafood"},
                    {"title": "Octopus Salad", "description": "Tender octopus with mixed greens and olive oil", "price": 20000, "category": "Salads"},
                    {"title": "Fish Soup", "description": "Clear fish broth with vegetables and herbs", "price": 12000, "category": "Soups"},
                    {"title": "Coconut Rice", "description": "Light coconut rice with minimal oil", "price": 8000, "category": "Rice"},
                    {"title": "Seaweed Salad", "description": "Nutritious seaweed with sesame dressing", "price": 10000, "category": "Salads"},
                ]
            },
            {
                "username": "green_garden",
                "restaurant_name": "Green Garden Vegetarian",
                "description": "100% plant-based healthy meals for vegetarians and vegans",
                "address": "Kariakoo, Dar es Salaam",
                "phone": "+255 754 123 004",
                "dishes": [
                    {"title": "Buddha Bowl", "description": "Mixed vegetables, chickpeas, quinoa, and tahini", "price": 14000, "category": "Bowls"},
                    {"title": "Vegetable Curry", "description": "Mixed vegetables in aromatic coconut curry", "price": 11000, "category": "Curry"},
                    {"title": "Avocado Toast", "description": "Whole grain bread with smashed avocado and seeds", "price": 9000, "category": "Breakfast"},
                    {"title": "Green Tea", "description": "Organic green tea with antioxidants", "price": 4000, "category": "Beverages"},
                    {"title": "Chia Pudding", "description": "Chia seeds with coconut milk and berries", "price": 8000, "category": "Desserts"},
                ]
            },
            {
                "username": "fitness_fuel",
                "restaurant_name": "Fitness Fuel Station",
                "description": "High-protein, low-carb meals designed for fitness enthusiasts",
                "address": "Oyster Bay, Dar es Salaam",
                "phone": "+255 754 123 005",
                "dishes": [
                    {"title": "Protein Power Plate", "description": "Grilled chicken, quinoa, and steamed broccoli", "price": 18000, "category": "Fitness"},
                    {"title": "Beef Steak Salad", "description": "Lean beef strips on mixed greens with nuts", "price": 22000, "category": "Salads"},
                    {"title": "Protein Smoothie", "description": "Whey protein, banana, and almond milk", "price": 10000, "category": "Beverages"},
                    {"title": "Egg White Omelette", "description": "Egg whites with vegetables and herbs", "price": 12000, "category": "Breakfast"},
                    {"title": "Greek Yogurt Bowl", "description": "Greek yogurt with nuts and berries", "price": 9000, "category": "Desserts"},
                ]
            }
        ]
        
        # Create sample users and restaurants
        for restaurant_data in restaurants_data:
            # Check if restaurant owner exists
            restaurant_owner = User.query.filter_by(username=restaurant_data["username"]).first()
            if not restaurant_owner:
                # Create restaurant owner
                restaurant_owner = User(
                    username=restaurant_data["username"],
                    email=f"{restaurant_data['username']}@msosihub.tz",
                    password_hash=generate_password_hash("restaurant123"),
                    first_name=restaurant_data["restaurant_name"].split()[0],
                    last_name="Owner",
                    phone=restaurant_data["phone"],
                    user_type="restaurant",
                    address=restaurant_data["address"]
                )
                db.session.add(restaurant_owner)
                db.session.commit()
                print(f"✅ Created restaurant owner: {restaurant_owner.username}")
            
            # Check if restaurant exists
            restaurant = Restaurant.query.filter_by(name=restaurant_data["restaurant_name"]).first()
            if not restaurant:
                # Create restaurant
                restaurant = Restaurant(
                    user_id=restaurant_owner.id,
                    name=restaurant_data["restaurant_name"],
                    description=restaurant_data["description"],
                    address=restaurant_data["address"],
                    phone=restaurant_data["phone"]
                )
                db.session.add(restaurant)
                db.session.commit()
                print(f"✅ Created restaurant: {restaurant.name}")
            
            # Create dishes
            for dish_data in restaurant_data["dishes"]:
                existing_dish = Dish.query.filter_by(
                    title=dish_data["title"], 
                    restaurant_id=restaurant.id
                ).first()
                
                if not existing_dish:
                    dish = Dish(
                        restaurant_id=restaurant.id,
                        title=dish_data["title"],
                        description=dish_data["description"],
                        price=dish_data["price"],
                        category=dish_data["category"],
                        inventory=50  # Default inventory
                    )
                    db.session.add(dish)
            
            db.session.commit()
            print(f"✅ Added {len(restaurant_data['dishes'])} dishes to {restaurant.name}")
        
        # Create sample customers
        sample_customers = [
            {
                "username": "john_customer",
                "email": "john@customer.com",
                "first_name": "John",
                "last_name": "Mwalimu",
                "phone": "+255 754 111 001",
                "address": "Kinondoni, Dar es Salaam"
            },
            {
                "username": "mary_customer",
                "email": "mary@customer.com",
                "first_name": "Mary",
                "last_name": "Kimani",
                "phone": "+255 754 111 002",
                "address": "Temeke, Dar es Salaam"
            }
        ]
        
        for customer_data in sample_customers:
            existing_customer = User.query.filter_by(username=customer_data["username"]).first()
            if not existing_customer:
                customer = User(
                    username=customer_data["username"],
                    email=customer_data["email"],
                    password_hash=generate_password_hash("customer123"),
                    first_name=customer_data["first_name"],
                    last_name=customer_data["last_name"],
                    phone=customer_data["phone"],
                    address=customer_data["address"],
                    user_type="customer",
                    wallet_balance=100000.0  # TZS 100k starting balance
                )
                db.session.add(customer)
                db.session.commit()
                print(f"✅ Created customer: {customer.username}")
        
        # Create sample driver
        existing_driver = User.query.filter_by(username="driver_hassan").first()
        if not existing_driver:
            driver = User(
                username="driver_hassan",
                email="hassan@driver.com",
                password_hash=generate_password_hash("driver123"),
                first_name="Hassan",
                last_name="Delivery",
                phone="+255 754 222 001",
                address="Ilala, Dar es Salaam",
                user_type="driver"
            )
            db.session.add(driver)
            db.session.commit()
            print(f"✅ Created driver: {driver.username}")
        
        print("\n🎉 Sample data created successfully!")
        print("=" * 60)
        print("📊 SUMMARY:")
        print(f"   👥 Users: {User.query.count()}")
        print(f"   🏪 Restaurants: {Restaurant.query.count()}")
        print(f"   🍽️  Dishes: {Dish.query.count()}")
        print("\n🔑 TEST ACCOUNTS:")
        print("   Admin: admin / admin123")
        print("   Restaurant: healthy_bites / restaurant123")
        print("   Customer: john_customer / customer123")
        print("   Driver: driver_hassan / driver123")
        print("=" * 60)

if __name__ == "__main__":
    create_sample_data()