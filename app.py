from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps

# Import email notifications
try:
    from notifications import send_notification, email_service
    EMAIL_ENABLED = True
    print("✅ Email notifications enabled")
except ImportError:
    EMAIL_ENABLED = False
    print("⚠️ Email notifications disabled - create notifications.py")
    def send_notification(user_id, message, notification_type="info", email_data=None):
        print(f"📱 NOTIFICATION [{notification_type.upper()}] to User {user_id}: {message}")
        return True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'msosihub-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///msosihub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    user_type = db.Column(db.String(20), default="customer")  # customer, restaurant, driver, admin
    wallet_balance = db.Column(db.Float, default=0.0)  # Monthly prepaid wallet
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='restaurants')
    dishes = db.relationship('Dish', backref='restaurant', lazy=True)

class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    is_available = db.Column(db.Boolean, default=True)
    inventory = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, confirmed, preparing, ready, out_for_delivery, delivered, cancelled
    payment_status = db.Column(db.String(20), default="pending")  # pending, paid, failed
    payment_method = db.Column(db.String(20), default="wallet")  # wallet, mpesa, airtel, tigo
    delivery_address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='orders')
    restaurant = db.relationship('Restaurant', backref='orders')
    driver = db.relationship('User', foreign_keys=[driver_id], backref='deliveries')
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey("dish.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    dish = db.relationship('Dish', backref='order_items')

# Forms
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    phone = StringField("Phone", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    address = TextAreaField("Address")
    user_type = SelectField("Account Type", choices=[
        ("customer", "Customer"),
        ("restaurant", "Restaurant Owner"),
        ("driver", "Delivery Driver")
    ])

class RestaurantForm(FlaskForm):
    name = StringField("Restaurant Name", validators=[DataRequired()])
    description = TextAreaField("Description")
    address = TextAreaField("Address", validators=[DataRequired()])
    phone = StringField("Phone", validators=[DataRequired()])

class DishForm(FlaskForm):
    title = StringField("Dish Name", validators=[DataRequired()])
    description = TextAreaField("Description")
    price = FloatField("Price (TZS)", validators=[DataRequired(), NumberRange(min=0)])
    category = StringField("Category")
    inventory = IntegerField("Inventory", validators=[NumberRange(min=0)], default=100)

# Helper Functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def get_cart_total():
    cart = session.get("cart", {})
    total_items = sum(item["quantity"] for item in cart.values())
    total_amount = sum(item["price"] * item["quantity"] for item in cart.values())
    return total_items, total_amount

def send_email_notification(user, notification_type, **kwargs):
    """Helper function to send email notifications"""
    if not EMAIL_ENABLED:
        return
    
    email_data = {'email': user.email, 'type': notification_type}
    email_data.update(kwargs)
    
    return send_notification(user.id, f"Email: {notification_type}", "email", email_data)

# Context Processor
@app.context_processor
def cart_context():
    context = {}
    if 'cart' in session:
        cart_count = sum(item['quantity'] for item in session['cart'].values())
        cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())
        context.update({'cart_count': cart_count, 'cart_total': cart_total})
    else:
        context.update({'cart_count': 0, 'cart_total': 0})
    
    # Add wallet balance to context if user is logged in
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            context['wallet_balance'] = user.wallet_balance
    
    return context

# Main Routes
@app.route("/")
def index():
    # Get featured dishes from all restaurants
    dishes = Dish.query.filter_by(is_available=True).limit(6).all()
    return render_template("index.html", dishes=dishes)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash("Username or email already exists!", "error")
            return render_template("register.html", form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            address=form.address.data,
            user_type=form.user_type.data,
            wallet_balance=50000.0 if form.user_type.data == "customer" else 0.0  # Free TZS 50k for new customers
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email based on user type
        if EMAIL_ENABLED:
            try:
                if form.user_type.data == "customer":
                    # Send customer welcome email with wallet bonus info
                    send_email_notification(user, 'welcome', name=f"{user.first_name} {user.last_name}")
                elif form.user_type.data == "restaurant":
                    # Send restaurant partner welcome email
                    send_email_notification(user, 'restaurant_welcome', restaurant_name=f"{user.first_name} {user.last_name}")
                elif form.user_type.data == "driver":
                    # Send driver welcome email
                    send_email_notification(user, 'driver_welcome', name=f"{user.first_name} {user.last_name}")
                
                print(f"✅ Welcome email sent to {user.email} ({user.user_type})")
            except Exception as e:
                print(f"⚠️ Failed to send welcome email to {user.email}: {str(e)}")
                # Don't fail registration if email fails
        else:
            print(f"📧 Email disabled - welcome email not sent to {user.email}")
        
        # Show appropriate success message based on user type
        if form.user_type.data == "customer":
            flash("Registration successful! You received TZS 50,000 welcome bonus! Check your email for details.", "success")
        elif form.user_type.data == "restaurant":
            flash("Registration successful! Welcome to MsosiHub Partner Network! Check your email for setup instructions.", "success")
        elif form.user_type.data == "driver":
            flash("Registration successful! Welcome to MsosiHub Delivery Team! Check your email for onboarding details.", "success")
        
        return redirect(url_for("login"))
    
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            session["user_id"] = user.id
            session["user_type"] = user.user_type
            session["username"] = user.username
            session["wallet_balance"] = user.wallet_balance
            
            flash(f"Welcome back, {user.first_name}!", "success")
            
            # Redirect based on user type
            if user.user_type == "restaurant":
                return redirect(url_for("restaurant_dashboard"))
            elif user.user_type == "driver":
                return redirect(url_for("driver_dashboard"))
            elif user.user_type == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("index"))
        else:
            flash("Invalid username or password!", "error")
    
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/restaurants")
def restaurants():
    restaurants_list = Restaurant.query.filter_by(is_active=True).all()
    return render_template("restaurants.html", restaurants=restaurants_list)

@app.route("/menu/<int:restaurant_id>")
def menu(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    dishes = Dish.query.filter_by(restaurant_id=restaurant_id, is_available=True).all()
    
    # Group dishes by category
    categories = {}
    for dish in dishes:
        category = dish.category or "Other"
        if category not in categories:
            categories[category] = []
        categories[category].append(dish)
    
    return render_template("menu.html", restaurant=restaurant, categories=categories)

# Cart Routes
@app.route("/cart")
@login_required
def cart():
    cart_items = session.get("cart", {})
    total = sum(item['price'] * item['quantity'] for item in cart_items.values())
    delivery_fee = 2000
    
    return render_template("cart.html", 
                         cart_items=cart_items, 
                         subtotal=total,
                         delivery_fee=delivery_fee,
                         total=total + delivery_fee)

@app.route("/update_cart_quantity", methods=["POST"])
@login_required
def update_cart_quantity():
    data = request.get_json()
    dish_id = str(data.get('dish_id'))
    new_quantity = int(data.get('quantity', 1))
    
    print(f"DEBUG: Updating cart quantity for dish {dish_id} to {new_quantity}")
    
    if 'cart' not in session or dish_id not in session['cart']:
        return jsonify({'success': False, 'message': 'Item not found in cart'}), 404
    
    # Validate quantity
    if new_quantity < 1:
        return jsonify({'success': False, 'message': 'Quantity must be at least 1'}), 400
    
    # Get current item details for debugging
    current_item = session['cart'][dish_id]
    print(f"DEBUG: Current item - Price: {current_item['price']}, Old Qty: {current_item['quantity']}, New Qty: {new_quantity}")
    
    # Update the quantity
    session['cart'][dish_id]['quantity'] = new_quantity
    session.modified = True
    
    # Recalculate cart totals
    cart_count = sum(item['quantity'] for item in session['cart'].values())
    cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())
    
    print(f"DEBUG: Cart totals - Count: {cart_count}, Total: {cart_total}")
    print(f"DEBUG: Cart items: {session['cart']}")
    
    return jsonify({
        'success': True,
        'message': f'Quantity updated to {new_quantity}',
        'cart_count': cart_count,
        'cart_total': cart_total
    })

@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    data = request.get_json()
    dish_id = str(data.get('dish_id'))
    quantity = int(data.get('quantity', 1))
    
    dish = Dish.query.get_or_404(dish_id)
    
    if 'cart' not in session:
        session['cart'] = {}
    
    # Check if cart has items from different restaurant
    current_cart = session['cart']
    if current_cart:
        first_item_id = next(iter(current_cart))
        first_dish = Dish.query.get(first_item_id)
        if first_dish and first_dish.restaurant_id != dish.restaurant_id:
            return jsonify({
                'success': False, 
                'message': 'You can only order from one restaurant at a time. Clear cart first.'
            }), 400
    
    # Add/update item
    if dish_id in current_cart:
        current_cart[dish_id]['quantity'] += quantity
    else:
        current_cart[dish_id] = {
            'title': dish.title,
            'price': float(dish.price),
            'quantity': quantity,
            'restaurant_id': dish.restaurant_id
        }
    
    session['cart'] = current_cart
    session.modified = True
    
    cart_count = sum(item['quantity'] for item in current_cart.values())
    cart_total = sum(item['price'] * item['quantity'] for item in current_cart.values())
    
    return jsonify({
        'success': True,
        'message': f'{dish.title} added to cart',
        'cart_count': cart_count,
        'cart_total': cart_total
    })

@app.route("/remove_from_cart", methods=["POST"])
@login_required
def remove_from_cart():
    data = request.get_json()
    dish_id = str(data.get('dish_id'))
    
    if 'cart' in session and dish_id in session['cart']:
        removed_item = session['cart'].pop(dish_id)
        session.modified = True
        
        cart_count = sum(item['quantity'] for item in session['cart'].values())
        cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())
        
        return jsonify({
            'success': True,
            'message': f'{removed_item["title"]} removed from cart',
            'cart_count': cart_count,
            'cart_total': cart_total
        })
    
    return jsonify({'success': False, 'message': 'Item not found in cart'}), 404

@app.route("/clear_cart", methods=["POST"])
@login_required
def clear_cart():
    session['cart'] = {}
    session.modified = True
    return jsonify({'success': True, 'message': 'Cart cleared', 'cart_count': 0, 'cart_total': 0})

# Order Routes
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items = session.get("cart", {})
    if not cart_items:
        flash("Your cart is empty!", "error")
        return redirect(url_for("restaurants"))
    
    if request.method == "POST":
        user = User.query.get(session["user_id"])
        cart_count, subtotal = get_cart_total()
        delivery_fee = 2000
        total_amount = subtotal + delivery_fee
        
        # Check wallet balance
        if user.wallet_balance < total_amount:
            flash(f"Insufficient wallet balance. You have TZS {user.wallet_balance:.2f}, need TZS {total_amount:.2f}", "error")
            return redirect(url_for("wallet"))
        
        # Get restaurant_id from cart
        restaurant_id = list(cart_items.values())[0]["restaurant_id"]
        
        # Create order
        order = Order(
            user_id=user.id,
            restaurant_id=restaurant_id,
            total_amount=total_amount,
            delivery_address=request.form.get("delivery_address", user.address),
            phone=request.form.get("phone", user.phone),
            payment_method="wallet",
            special_instructions=request.form.get("special_instructions", "")
        )
        
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for dish_id, item in cart_items.items():
            order_item = OrderItem(
                order_id=order.id,
                dish_id=int(dish_id),
                quantity=item["quantity"],
                price=item["price"]
            )
            db.session.add(order_item)
        
        # Deduct from wallet and confirm payment
        user.wallet_balance -= total_amount
        session["wallet_balance"] = user.wallet_balance
        order.payment_status = "paid"
        order.status = "confirmed"
        
        db.session.commit()
        
        # Prepare email data for order confirmation
        if EMAIL_ENABLED:
            # Prepare order data for email
            order_data = {
                'id': order.id,
                'total': total_amount,
                'subtotal': subtotal,
                'delivery_address': order.delivery_address,
                'phone': order.phone
            }
            
            # Prepare items data for email
            items_data = []
            for dish_id, item in cart_items.items():
                items_data.append({
                    'name': item['title'],
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'total': item['price'] * item['quantity']
                })
            
            # Prepare restaurant data for email
            restaurant_data = {
                'name': Restaurant.query.get(restaurant_id).name
            }
            
            # Send order confirmation email to customer
            send_email_notification(
                user, 'order_confirmation',
                customer_name=f"{user.first_name} {user.last_name}",
                order=order_data,
                items=items_data,
                restaurant=restaurant_data
            )
            
            # Send new order notification to restaurant
            restaurant = Restaurant.query.get(restaurant_id)
            restaurant_owner = User.query.get(restaurant.user_id)
            send_email_notification(
                restaurant_owner, 'new_order_restaurant',
                customer_name=f"{user.first_name} {user.last_name}",
                order=order_data,
                items=items_data
            )
        
        # Send notifications
        send_notification(user.id, f"Order #{order.id} confirmed! Total: TZS {total_amount:.2f}", "success")
        
        # Clear cart
        session.pop("cart", None)
        
        flash("Order placed successfully!", "success")
        return redirect(url_for("order_success", order_id=order.id))
    
    user = User.query.get(session["user_id"])
    cart_count, subtotal = get_cart_total()
    delivery_fee = 2000
    total = subtotal + delivery_fee
    
    return render_template("checkout.html", 
                         cart_items=cart_items, 
                         subtotal=subtotal,
                         delivery_fee=delivery_fee,
                         total=total, 
                         user=user)

@app.route("/order_success/<int:order_id>")
@login_required
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session["user_id"]:
        flash("Order not found!", "error")
        return redirect(url_for("index"))
    
    return render_template("order_success.html", order=order)

@app.route("/my_orders")
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=session["user_id"]).order_by(Order.created_at.desc()).all()
    return render_template("my_orders.html", orders=orders)

# Wallet Routes
@app.route("/wallet")
@login_required
def wallet():
    user = User.query.get(session["user_id"])
    return render_template("wallet.html", user=user)

@app.route("/recharge_wallet", methods=["POST"])
@login_required
def recharge_wallet():
    amount = float(request.form.get("amount", 0))
    if amount > 0:
        user = User.query.get(session["user_id"])
        user.wallet_balance += amount
        session["wallet_balance"] = user.wallet_balance
        db.session.commit()
        
        # Send wallet recharge email notification
        if EMAIL_ENABLED:
            send_email_notification(
                user, 'wallet_recharge',
                customer_name=f"{user.first_name} {user.last_name}",
                amount=amount,
                new_balance=user.wallet_balance,
                payment_method=request.form.get('payment_method', 'Mobile Money')
            )
        
        send_notification(user.id, f"Wallet recharged with TZS {amount:.2f}. New balance: TZS {user.wallet_balance:.2f}", "success")
        flash(f"Wallet recharged with TZS {amount:.2f}!", "success")
    
    return redirect(url_for("wallet"))

# Restaurant Dashboard
@app.route("/restaurant_dashboard")
@login_required
def restaurant_dashboard():
    if session.get("user_type") != "restaurant":
        flash("Access denied. Restaurant account required.", "error")
        return redirect(url_for("index"))
    
    user = User.query.get(session["user_id"])
    restaurant = Restaurant.query.filter_by(user_id=user.id).first()
    
    if not restaurant:
        return redirect(url_for("setup_restaurant"))
    
    # Get recent orders
    recent_orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).limit(10).all()
    
    # Get statistics
    stats = {
        "total_orders": Order.query.filter_by(restaurant_id=restaurant.id).count(),
        "pending_orders": Order.query.filter_by(restaurant_id=restaurant.id, status="pending").count(),
        "total_revenue": db.session.query(db.func.sum(Order.total_amount)).filter_by(restaurant_id=restaurant.id, payment_status="paid").scalar() or 0,
        "menu_items": Dish.query.filter_by(restaurant_id=restaurant.id).count()
    }
    
    return render_template("restaurant_dashboard.html", restaurant=restaurant, orders=recent_orders, stats=stats)

@app.route("/setup_restaurant", methods=["GET", "POST"])
@login_required
def setup_restaurant():
    if session.get("user_type") != "restaurant":
        flash("Access denied. Restaurant account required.", "error")
        return redirect(url_for("index"))
    
    form = RestaurantForm()
    if form.validate_on_submit():
        user = User.query.get(session["user_id"])
        restaurant = Restaurant(
            user_id=session["user_id"],
            name=form.name.data,
            description=form.description.data,
            address=form.address.data,
            phone=form.phone.data
        )
        
        db.session.add(restaurant)
        db.session.commit()
        
        # Send restaurant welcome email
        if EMAIL_ENABLED:
            send_email_notification(
                user, 'restaurant_welcome',
                restaurant_name=restaurant.name
            )
        
        flash("Restaurant setup completed!", "success")
        return redirect(url_for("restaurant_dashboard"))
    
    return render_template("setup_restaurant.html", form=form)

@app.route("/manage_menu")
@login_required
def manage_menu():
    if session.get("user_type") != "restaurant":
        flash("Access denied.", "error")
        return redirect(url_for("index"))
    
    user = User.query.get(session["user_id"])
    restaurant = Restaurant.query.filter_by(user_id=user.id).first()
    
    if not restaurant:
        return redirect(url_for("setup_restaurant"))
    
    dishes = Dish.query.filter_by(restaurant_id=restaurant.id).all()
    return render_template("manage_menu.html", dishes=dishes, restaurant=restaurant)

@app.route("/add_dish", methods=["GET", "POST"])
@login_required
def add_dish():
    if session.get("user_type") != "restaurant":
        flash("Access denied.", "error")
        return redirect(url_for("index"))
    
    user = User.query.get(session["user_id"])
    restaurant = Restaurant.query.filter_by(user_id=user.id).first()
    
    if not restaurant:
        return redirect(url_for("setup_restaurant"))
    
    form = DishForm()
    if form.validate_on_submit():
        dish = Dish(
            restaurant_id=restaurant.id,
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            inventory=form.inventory.data
        )
        
        db.session.add(dish)
        db.session.commit()
        
        flash("Dish added successfully!", "success")
        return redirect(url_for("manage_menu"))
    
    return render_template("add_dish.html", form=form, restaurant=restaurant)

# Driver Dashboard
@app.route("/driver_dashboard")
@login_required
def driver_dashboard():
    if session.get("user_type") != "driver":
        flash("Access denied. Driver account required.", "error")
        return redirect(url_for("index"))
    
    # Get available orders for delivery
    available_orders = Order.query.filter_by(status="ready", driver_id=None).all()
    my_deliveries = Order.query.filter_by(driver_id=session["user_id"]).order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template("driver_dashboard.html", available_orders=available_orders, my_deliveries=my_deliveries)

@app.route("/take_delivery/<int:order_id>", methods=["POST"])
@login_required
def take_delivery(order_id):
    if session.get("user_type") != "driver":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    order = Order.query.get_or_404(order_id)
    if order.driver_id is None and order.status == "ready":
        order.driver_id = session["user_id"]
        order.status = "out_for_delivery"
        db.session.commit()
        
        send_notification(order.user_id, f"Your order #{order.id} is out for delivery!", "info")
        
        return jsonify({"success": True, "message": "Delivery accepted"})
    
    return jsonify({"success": False, "message": "Order not available"}), 400

@app.route("/mark_delivered/<int:order_id>", methods=["POST"])
@login_required
def mark_delivered(order_id):
    if session.get("user_type") != "driver":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    order = Order.query.get_or_404(order_id)
    if order.driver_id == session["user_id"] and order.status == "out_for_delivery":
        order.status = "delivered"
        db.session.commit()
        
        send_notification(order.user_id, f"Your order #{order.id} has been delivered! Enjoy your meal!", "success")
        
        return jsonify({"success": True, "message": "Order marked as delivered"})
    
    return jsonify({"success": False, "message": "Invalid order"}), 400

# Admin Dashboard
@app.route("/admin_dashboard")
@login_required
def admin_dashboard():
    if session.get("user_type") != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("index"))
    
    stats = {
        "total_users": User.query.count(),
        "total_restaurants": Restaurant.query.count(),
        "total_orders": Order.query.count(),
        "total_revenue": db.session.query(db.func.sum(Order.total_amount)).filter_by(payment_status="paid").scalar() or 0
    }
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template("admin_dashboard.html", stats=stats, recent_orders=recent_orders)

# Admin Order Management
@app.route("/admin/orders")
@login_required
def admin_orders():
    if session.get("user_type") != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("index"))
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    restaurant_filter = request.args.get('restaurant', '')
    date_filter = request.args.get('date', '')
    
    # Build query
    query = Order.query
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    if restaurant_filter:
        query = query.join(Restaurant).filter(Restaurant.name.ilike(f'%{restaurant_filter}%'))
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d')
            query = query.filter(db.func.date(Order.created_at) == filter_date.date())
        except ValueError:
            pass
    
    # Get paginated results
    page = request.args.get('page', 1, type=int)
    per_page = 20
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get all restaurants for filter dropdown
    restaurants = Restaurant.query.all()
    
    return render_template("admin_orders.html", 
                         orders=orders, 
                         restaurants=restaurants,
                         status_filter=status_filter,
                         restaurant_filter=restaurant_filter,
                         date_filter=date_filter)

@app.route("/admin/order/<int:order_id>")
@login_required
def admin_order_details(order_id):
    if session.get("user_type") != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("index"))
    
    order = Order.query.get_or_404(order_id)
    
    # Get order items with dish details
    order_items = OrderItem.query.filter_by(order_id=order_id).all()
    
    return render_template("admin_order_details.html", order=order, order_items=order_items)

@app.route("/api/admin/order/<int:order_id>", methods=["GET"])
@login_required
def api_admin_order_details(order_id):
    if session.get("user_type") != "admin":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    order = Order.query.get_or_404(order_id)
    order_items = OrderItem.query.filter_by(order_id=order_id).all()
    
    # Prepare order data for JSON response
    order_data = {
        "id": order.id,
        "customer": {
            "name": f"{order.user.first_name} {order.user.last_name}",
            "email": order.user.email,
            "phone": order.user.phone
        },
        "restaurant": {
            "name": order.restaurant.name,
            "phone": order.restaurant.phone
        },
        "delivery_address": order.delivery_address,
        "phone": order.phone,
        "total_amount": order.total_amount,
        "status": order.status,
        "payment_status": order.payment_status,
        "payment_method": order.payment_method,
        "special_instructions": order.special_instructions,
        "created_at": order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "driver": None
    }
    
    if order.driver:
        order_data["driver"] = {
            "name": f"{order.driver.first_name} {order.driver.last_name}",
            "phone": order.driver.phone
        }
    
    # Prepare items data
    items_data = []
    for item in order_items:
        items_data.append({
            "dish_name": item.dish.title,
            "quantity": item.quantity,
            "price": item.price,
            "total": item.price * item.quantity
        })
    
    order_data["items"] = items_data
    
    return jsonify({"success": True, "order": order_data})

@app.route("/api/admin/update_order_status", methods=["POST"])
@login_required
def api_admin_update_order_status():
    if session.get("user_type") != "admin":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    data = request.get_json()
    order_id = data.get("order_id")
    new_status = data.get("status")
    notes = data.get("notes", "")
    
    order = Order.query.get_or_404(order_id)
    old_status = order.status
    order.status = new_status
    
    # Add admin notes if provided
    if notes:
        # You could add a notes field to the Order model or create a separate OrderNotes model
        pass
    
    db.session.commit()
    
    # Send notification to customer about status update
    send_notification(order.user_id, f"Order #{order.id} status updated from {old_status} to {new_status}", "info")
    
    # Send email notification if enabled
    if EMAIL_ENABLED:
        customer = User.query.get(order.user_id)
        send_email_notification(
            customer, 'order_status',
            customer_name=f"{customer.first_name} {customer.last_name}",
            order_id=order.id,
            status=new_status
        )
    
    return jsonify({
        "success": True, 
        "message": f"Order #{order.id} status updated to {new_status}",
        "new_status": new_status
    })

@app.route("/api/toggle_dish_availability", methods=["POST"])
@login_required
def toggle_dish_availability():
    if session.get("user_type") != "restaurant":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    data = request.get_json()
    dish_id = data.get("dish_id")
    is_available = data.get("is_available")
    
    dish = Dish.query.get_or_404(dish_id)
    
    # Check if user owns this restaurant
    restaurant = Restaurant.query.filter_by(user_id=session["user_id"]).first()
    if dish.restaurant_id != restaurant.id:
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    dish.is_available = is_available
    db.session.commit()
    
    return jsonify({"success": True, "message": "Dish availability updated"})

@app.route("/api/delete_dish", methods=["POST"])
@login_required
def delete_dish():
    if session.get("user_type") != "restaurant":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    data = request.get_json()
    dish_id = data.get("dish_id")
    
    dish = Dish.query.get_or_404(dish_id)
    
    # Check if user owns this restaurant
    restaurant = Restaurant.query.filter_by(user_id=session["user_id"]).first()
    if dish.restaurant_id != restaurant.id:
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    db.session.delete(dish)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Dish deleted successfully"})

# Admin User Management
@app.route("/admin/users")
@login_required
def admin_users():
    if session.get("user_type") != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("index"))
    
    # Get filter parameters
    user_type_filter = request.args.get('user_type', '')
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # Build query
    query = User.query
    
    if user_type_filter:
        query = query.filter(User.user_type == user_type_filter)
    
    if status_filter == 'active':
        # For now, we'll consider all users active since we don't have a status field
        pass
    elif status_filter == 'inactive':
        # This would filter inactive users if we had a status field
        pass
    
    if search_query:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%'),
                User.first_name.ilike(f'%{search_query}%'),
                User.last_name.ilike(f'%{search_query}%')
            )
        )
    
    # Get paginated results
    page = request.args.get('page', 1, type=int)
    per_page = 20
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template("admin_users.html", 
                         users=users,
                         user_type_filter=user_type_filter,
                         status_filter=status_filter,
                         search_query=search_query)

@app.route("/admin/user/<int:user_id>")
@login_required
def admin_user_details(user_id):
    if session.get("user_type") != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("index"))
    
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    user_stats = {
        "total_orders": Order.query.filter_by(user_id=user_id).count(),
        "total_spent": db.session.query(db.func.sum(Order.total_amount)).filter_by(user_id=user_id, payment_status="paid").scalar() or 0,
        "restaurants_owned": Restaurant.query.filter_by(user_id=user_id).count(),
        "deliveries_completed": Order.query.filter_by(driver_id=user_id, status="delivered").count()
    }
    
    # Get recent orders
    recent_orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).limit(5).all()
    
    # Get restaurants owned (if user is restaurant owner)
    restaurants_owned = Restaurant.query.filter_by(user_id=user_id).all()
    
    return render_template("admin_user_details.html", 
                         user=user, 
                         user_stats=user_stats,
                         recent_orders=recent_orders,
                         restaurants_owned=restaurants_owned)

@app.route("/api/admin/user/<int:user_id>", methods=["GET"])
@login_required
def api_admin_user_details(user_id):
    if session.get("user_type") != "admin":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    user_stats = {
        "total_orders": Order.query.filter_by(user_id=user_id).count(),
        "total_spent": db.session.query(db.func.sum(Order.total_amount)).filter_by(user_id=user_id, payment_status="paid").scalar() or 0,
        "restaurants_owned": Restaurant.query.filter_by(user_id=user_id).count(),
        "deliveries_completed": Order.query.filter_by(driver_id=user_id, status="delivered").count()
    }
    
    # Prepare user data for JSON response
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "address": user.address,
        "user_type": user.user_type,
        "wallet_balance": user.wallet_balance,
        "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "stats": user_stats
    }
    
    return jsonify({"success": True, "user": user_data})

@app.route("/api/admin/update_user_status", methods=["POST"])
@login_required
def api_admin_update_user_status():
    if session.get("user_type") != "admin":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    data = request.get_json()
    user_id = data.get("user_id")
    action = data.get("action")  # "activate", "deactivate", "change_type"
    new_user_type = data.get("new_user_type", "")
    notes = data.get("notes", "")
    
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from modifying themselves
    if user.id == session.get("user_id"):
        return jsonify({"success": False, "message": "Cannot modify your own account"}), 400
    
    if action == "change_type" and new_user_type:
        old_type = user.user_type
        user.user_type = new_user_type
        db.session.commit()
        
        # Send notification to user about account type change
        send_notification(user_id, f"Your account type has been changed from {old_type} to {new_user_type}", "info")
        
        return jsonify({
            "success": True, 
            "message": f"User {user.username} account type changed to {new_user_type}",
            "new_user_type": new_user_type
        })
    
    elif action == "reset_wallet":
        old_balance = user.wallet_balance
        user.wallet_balance = 0.0
        db.session.commit()
        
        # Send notification to user about wallet reset
        send_notification(user_id, f"Your wallet balance has been reset from TZS {old_balance:,.0f} to TZS 0", "warning")
        
        return jsonify({
            "success": True, 
            "message": f"User {user.username} wallet balance reset to TZS 0",
            "new_balance": 0.0
        })
    
    elif action == "add_wallet_balance":
        amount = data.get("amount", 0)
        if amount > 0:
            user.wallet_balance += amount
            db.session.commit()
            
            # Send notification to user about wallet credit
            send_notification(user_id, f"TZS {amount:,.0f} has been added to your wallet balance", "success")
            
            return jsonify({
                "success": True, 
                "message": f"TZS {amount:,.0f} added to {user.username}'s wallet",
                "new_balance": user.wallet_balance
            })
        else:
            return jsonify({"success": False, "message": "Invalid amount"}), 400
    
    return jsonify({"success": False, "message": "Invalid action"}), 400

@app.route("/api/admin/delete_user", methods=["POST"])
@login_required
def api_admin_delete_user():
    if session.get("user_type") != "admin":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    data = request.get_json()
    user_id = data.get("user_id")
    
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user.id == session.get("user_id"):
        return jsonify({"success": False, "message": "Cannot delete your own account"}), 400
    
    # Check if user has any active orders
    active_orders = Order.query.filter_by(user_id=user_id).filter(
        Order.status.in_(['pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery'])
    ).count()
    
    if active_orders > 0:
        return jsonify({"success": False, "message": f"Cannot delete user with {active_orders} active orders"}), 400
    
    # Delete user's data (cascade will handle related records)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        "success": True, 
        "message": f"User {user.username} has been deleted successfully"
    })

# Admin Reports
@app.route("/admin/reports")
@login_required
def admin_reports():
    if session.get("user_type") != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("index"))
    
    # Get date range parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    report_type = request.args.get('type', 'overview')
    
    # Calculate date range
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            start_dt = datetime.now() - timedelta(days=30)
            end_dt = datetime.now()
    else:
        # Default to last 30 days
        start_dt = datetime.now() - timedelta(days=30)
        end_dt = datetime.now()
    
    # Get basic statistics
    stats = {
        "total_users": User.query.count(),
        "total_restaurants": Restaurant.query.count(),
        "total_orders": Order.query.count(),
        "total_revenue": db.session.query(db.func.sum(Order.total_amount)).filter_by(payment_status="paid").scalar() or 0
    }
    
    # Get date range statistics
    range_stats = {
        "orders_in_range": Order.query.filter(
            Order.created_at >= start_dt,
            Order.created_at < end_dt
        ).count(),
        "revenue_in_range": db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.payment_status == "paid"
        ).scalar() or 0,
        "new_users_in_range": User.query.filter(
            User.created_at >= start_dt,
            User.created_at < end_dt
        ).count(),
        "new_restaurants_in_range": Restaurant.query.filter(
            Restaurant.created_at >= start_dt,
            Restaurant.created_at < end_dt
        ).count()
    }
    
    # Get order status distribution
    order_status_stats = db.session.query(
        Order.status,
        db.func.count(Order.id)
    ).filter(
        Order.created_at >= start_dt,
        Order.created_at < end_dt
    ).group_by(Order.status).all()
    
    # Get user type distribution
    user_type_stats = db.session.query(
        User.user_type,
        db.func.count(User.id)
    ).group_by(User.user_type).all()
    
    # Get top restaurants by orders
    top_restaurants = db.session.query(
        Restaurant.name,
        db.func.count(Order.id).label('order_count'),
        db.func.sum(Order.total_amount).label('total_revenue')
    ).join(Order).filter(
        Order.created_at >= start_dt,
        Order.created_at < end_dt
    ).group_by(Restaurant.id, Restaurant.name).order_by(
        db.func.count(Order.id).desc()
    ).limit(10).all()
    
    # Get daily order trends
    daily_orders = db.session.query(
        db.func.date(Order.created_at).label('date'),
        db.func.count(Order.id).label('order_count'),
        db.func.sum(Order.total_amount).label('daily_revenue')
    ).filter(
        Order.created_at >= start_dt,
        Order.created_at < end_dt
    ).group_by(db.func.date(Order.created_at)).order_by(
        db.func.date(Order.created_at)
    ).all()
    
    # Get recent activity
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template("admin_reports.html",
                         stats=stats,
                         range_stats=range_stats,
                         order_status_stats=order_status_stats,
                         user_type_stats=user_type_stats,
                         top_restaurants=top_restaurants,
                         daily_orders=daily_orders,
                         recent_orders=recent_orders,
                         recent_users=recent_users,
                         start_date=start_date or start_dt.strftime('%Y-%m-%d'),
                         end_date=end_date or (end_dt - timedelta(days=1)).strftime('%Y-%m-%d'),
                         report_type=report_type)

@app.route("/api/admin/reports/data")
@login_required
def api_admin_reports_data():
    if session.get("user_type") != "admin":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    # Get parameters
    report_type = request.args.get('type', 'overview')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Calculate date range
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            start_dt = datetime.now() - timedelta(days=30)
            end_dt = datetime.now()
    else:
        start_dt = datetime.now() - timedelta(days=30)
        end_dt = datetime.now()
    
    if report_type == 'revenue':
        # Revenue data
        daily_revenue = db.session.query(
            db.func.date(Order.created_at).label('date'),
            db.func.sum(Order.total_amount).label('revenue')
        ).filter(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.payment_status == "paid"
        ).group_by(db.func.date(Order.created_at)).order_by(
            db.func.date(Order.created_at)
        ).all()
        
        return jsonify({
            "success": True,
            "data": {
                "labels": [str(item.date) for item in daily_revenue],
                "values": [float(item.revenue) for item in daily_revenue]
            }
        })
    
    elif report_type == 'orders':
        # Order data
        daily_orders = db.session.query(
            db.func.date(Order.created_at).label('date'),
            db.func.count(Order.id).label('order_count')
        ).filter(
            Order.created_at >= start_dt,
            Order.created_at < end_dt
        ).group_by(db.func.date(Order.created_at)).order_by(
            db.func.date(Order.created_at)
        ).all()
        
        return jsonify({
            "success": True,
            "data": {
                "labels": [str(item.date) for item in daily_orders],
                "values": [int(item.order_count) for item in daily_orders]
            }
        })
    
    elif report_type == 'users':
        # User registration data
        daily_users = db.session.query(
            db.func.date(User.created_at).label('date'),
            db.func.count(User.id).label('user_count')
        ).filter(
            User.created_at >= start_dt,
            User.created_at < end_dt
        ).group_by(db.func.date(User.created_at)).order_by(
            db.func.date(User.created_at)
        ).all()
        
        return jsonify({
            "success": True,
            "data": {
                "labels": [str(item.date) for item in daily_users],
                "values": [int(item.user_count) for item in daily_users]
            }
        })
    
    return jsonify({"success": False, "message": "Invalid report type"}), 400

@app.route("/admin/reports/export")
@login_required
def admin_reports_export():
    if session.get("user_type") != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("index"))
    
    report_type = request.args.get('type', 'orders')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Calculate date range
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            start_dt = datetime.now() - timedelta(days=30)
            end_dt = datetime.now()
    else:
        start_dt = datetime.now() - timedelta(days=30)
        end_dt = datetime.now()
    
    if report_type == 'orders':
        # Export orders report
        orders = Order.query.filter(
            Order.created_at >= start_dt,
            Order.created_at < end_dt
        ).order_by(Order.created_at.desc()).all()
        
        # Create CSV data
        csv_data = "Order ID,Customer,Restaurant,Amount,Status,Payment Status,Date\n"
        for order in orders:
            csv_data += f"{order.id},{order.user.first_name} {order.user.last_name},{order.restaurant.name},{order.total_amount},{order.status},{order.payment_status},{order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = f"attachment; filename=orders_report_{start_date}_to_{end_date}.csv"
        response.headers["Content-Type"] = "text/csv"
        return response
    
    elif report_type == 'users':
        # Export users report
        users = User.query.filter(
            User.created_at >= start_dt,
            User.created_at < end_dt
        ).order_by(User.created_at.desc()).all()
        
        # Create CSV data
        csv_data = "User ID,Name,Username,Email,Type,Wallet Balance,Joined\n"
        for user in users:
            csv_data += f"{user.id},{user.first_name} {user.last_name},{user.username},{user.email},{user.user_type},{user.wallet_balance},{user.created_at.strftime('%Y-%m-%d')}\n"
        
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = f"attachment; filename=users_report_{start_date}_to_{end_date}.csv"
        response.headers["Content-Type"] = "text/csv"
        return response
    
    elif report_type == 'revenue':
        # Export revenue report
        orders = Order.query.filter(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.payment_status == "paid"
        ).order_by(Order.created_at.desc()).all()
        
        # Create CSV data
        csv_data = "Date,Order ID,Customer,Restaurant,Amount\n"
        for order in orders:
            csv_data += f"{order.created_at.strftime('%Y-%m-%d')},{order.id},{order.user.first_name} {order.user.last_name},{order.restaurant.name},{order.total_amount}\n"
        
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = f"attachment; filename=revenue_report_{start_date}_to_{end_date}.csv"
        response.headers["Content-Type"] = "text/csv"
        return response
    
    flash("Invalid report type", "error")
    return redirect(url_for("admin_reports"))

# Admin Restaurant Management
@app.route("/admin/restaurants")
@login_required
def admin_restaurants():
    if session.get("user_type") != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("index"))
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # Build query
    query = Restaurant.query
    
    if status_filter == 'active':
        query = query.filter(Restaurant.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(Restaurant.is_active == False)
    
    if search_query:
        query = query.filter(
            db.or_(
                Restaurant.name.ilike(f'%{search_query}%'),
                Restaurant.address.ilike(f'%{search_query}%'),
                Restaurant.phone.ilike(f'%{search_query}%')
            )
        )
    
    # Get paginated results
    page = request.args.get('page', 1, type=int)
    per_page = 20
    restaurants = query.order_by(Restaurant.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template("admin_restaurants.html", 
                         restaurants=restaurants,
                         status_filter=status_filter,
                         search_query=search_query)

@app.route("/admin/restaurant/<int:restaurant_id>")
@login_required
def admin_restaurant_details(restaurant_id):
    if session.get("user_type") != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("index"))
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    # Get restaurant statistics
    restaurant_stats = {
        "total_orders": Order.query.filter_by(restaurant_id=restaurant_id).count(),
        "total_revenue": db.session.query(db.func.sum(Order.total_amount)).filter_by(restaurant_id=restaurant_id, payment_status="paid").scalar() or 0,
        "total_dishes": Dish.query.filter_by(restaurant_id=restaurant_id).count(),
        "active_dishes": Dish.query.filter_by(restaurant_id=restaurant_id, is_available=True).count()
    }
    
    # Get recent orders
    recent_orders = Order.query.filter_by(restaurant_id=restaurant_id).order_by(Order.created_at.desc()).limit(10).all()
    
    # Get all dishes
    dishes = Dish.query.filter_by(restaurant_id=restaurant_id).order_by(Dish.created_at.desc()).all()
    
    return render_template("admin_restaurant_details.html", 
                         restaurant=restaurant,
                         restaurant_stats=restaurant_stats,
                         recent_orders=recent_orders,
                         dishes=dishes)

@app.route("/api/admin/restaurant/<int:restaurant_id>", methods=["GET"])
@login_required
def api_admin_restaurant_details(restaurant_id):
    if session.get("user_type") != "admin":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    # Get restaurant statistics
    restaurant_stats = {
        "total_orders": Order.query.filter_by(restaurant_id=restaurant_id).count(),
        "total_revenue": db.session.query(db.func.sum(Order.total_amount)).filter_by(restaurant_id=restaurant_id, payment_status="paid").scalar() or 0,
        "total_dishes": Dish.query.filter_by(restaurant_id=restaurant_id).count(),
        "active_dishes": Dish.query.filter_by(restaurant_id=restaurant_id, is_available=True).count()
    }
    
    # Prepare restaurant data for JSON response
    restaurant_data = {
        "id": restaurant.id,
        "name": restaurant.name,
        "description": restaurant.description,
        "address": restaurant.address,
        "phone": restaurant.phone,
        "is_active": restaurant.is_active,
        "created_at": restaurant.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "owner": {
            "name": f"{restaurant.user.first_name} {restaurant.user.last_name}",
            "email": restaurant.user.email,
            "phone": restaurant.user.phone
        },
        "stats": restaurant_stats
    }
    
    return jsonify({"success": True, "restaurant": restaurant_data})

@app.route("/api/admin/update_restaurant_status", methods=["POST"])
@login_required
def api_admin_update_restaurant_status():
    if session.get("user_type") != "admin":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    data = request.get_json()
    restaurant_id = data.get("restaurant_id")
    action = data.get("action")  # "activate", "deactivate", "update_info"
    new_name = data.get("name", "")
    new_description = data.get("description", "")
    new_address = data.get("address", "")
    new_phone = data.get("phone", "")
    notes = data.get("notes", "")
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    if action == "activate":
        restaurant.is_active = True
        db.session.commit()
        
        # Send notification to restaurant owner
        send_notification(restaurant.user_id, f"Your restaurant '{restaurant.name}' has been activated by admin", "success")
        
        return jsonify({
            "success": True, 
            "message": f"Restaurant '{restaurant.name}' activated successfully"
        })
    
    elif action == "deactivate":
        restaurant.is_active = False
        db.session.commit()
        
        # Send notification to restaurant owner
        send_notification(restaurant.user_id, f"Your restaurant '{restaurant.name}' has been deactivated by admin", "warning")
        
        return jsonify({
            "success": True, 
            "message": f"Restaurant '{restaurant.name}' deactivated successfully"
        })
    
    elif action == "update_info":
        old_name = restaurant.name
        restaurant.name = new_name
        restaurant.description = new_description
        restaurant.address = new_address
        restaurant.phone = new_phone
        db.session.commit()
        
        # Send notification to restaurant owner
        send_notification(restaurant.user_id, f"Your restaurant information has been updated by admin", "info")
        
        return jsonify({
            "success": True, 
            "message": f"Restaurant '{old_name}' information updated successfully"
        })
    
    return jsonify({"success": False, "message": "Invalid action"}), 400

@app.route("/api/admin/delete_restaurant", methods=["POST"])
@login_required
def api_admin_delete_restaurant():
    if session.get("user_type") != "admin":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    data = request.get_json()
    restaurant_id = data.get("restaurant_id")
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    # Check if restaurant has any active orders
    active_orders = Order.query.filter_by(restaurant_id=restaurant_id).filter(
        Order.status.in_(['pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery'])
    ).count()
    
    if active_orders > 0:
        return jsonify({"success": False, "message": f"Cannot delete restaurant with {active_orders} active orders"}), 400
    
    # Check if restaurant has any dishes
    dish_count = Dish.query.filter_by(restaurant_id=restaurant_id).count()
    
    restaurant_name = restaurant.name
    owner_id = restaurant.user_id
    
    # Delete restaurant and related data (cascade will handle dishes)
    db.session.delete(restaurant)
    db.session.commit()
    
    # Send notification to restaurant owner
    send_notification(owner_id, f"Your restaurant '{restaurant_name}' has been deleted by admin", "warning")
    
    return jsonify({
        "success": True, 
        "message": f"Restaurant '{restaurant_name}' has been deleted successfully"
    })

# Driver Map Routes
@app.route("/driver/map")
@login_required
def driver_map():
    if session.get("user_type") != "driver":
        flash("Access denied. Driver account required.", "error")
        return redirect(url_for("index"))
    
    # Get driver's active deliveries
    active_deliveries = Order.query.filter_by(
        driver_id=session.get("user_id"),
        status="out_for_delivery"
    ).all()
    
    # Get available orders for pickup
    available_orders = Order.query.filter_by(status="ready").all()
    
    return render_template("driver_map.html", 
                         active_deliveries=active_deliveries,
                         available_orders=available_orders)

@app.route("/api/driver/location", methods=["POST"])
@login_required
def update_driver_location():
    if session.get("user_type") != "driver":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    data = request.get_json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    
    if not latitude or not longitude:
        return jsonify({"success": False, "message": "Invalid coordinates"}), 400
    
    # In a real app, you would store this in a DriverLocation table
    # For now, we'll just return success
    return jsonify({
        "success": True,
        "message": "Location updated successfully"
    })

@app.route("/api/driver/deliveries")
@login_required
def get_driver_deliveries():
    if session.get("user_type") != "driver":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    # Get driver's active deliveries
    active_deliveries = Order.query.filter_by(
        driver_id=session.get("user_id"),
        status="out_for_delivery"
    ).all()
    
    deliveries_data = []
    for delivery in active_deliveries:
        # In a real app, you would have actual coordinates
        # For demo purposes, we'll use placeholder coordinates
        deliveries_data.append({
            "id": delivery.id,
            "restaurant_name": delivery.restaurant.name,
            "customer_name": f"{delivery.user.first_name} {delivery.user.last_name}",
            "delivery_address": delivery.delivery_address,
            "restaurant_address": delivery.restaurant.address,
            "restaurant_coords": {
                "lat": -6.8235,  # Dar es Salaam coordinates
                "lng": 39.2695
            },
            "delivery_coords": {
                "lat": -6.8235 + (delivery.id * 0.001),  # Slightly offset for demo
                "lng": 39.2695 + (delivery.id * 0.001)
            },
            "total_amount": delivery.total_amount,
            "created_at": delivery.created_at.strftime('%I:%M %p')
        })
    
    return jsonify({
        "success": True,
        "deliveries": deliveries_data
    })

@app.route("/api/driver/available-orders")
@login_required
def get_available_orders():
    if session.get("user_type") != "driver":
        return jsonify({"success": False, "message": "Access denied"}), 403
    
    # Get available orders for pickup
    available_orders = Order.query.filter_by(status="ready").all()
    
    orders_data = []
    for order in available_orders:
        orders_data.append({
            "id": order.id,
            "restaurant_name": order.restaurant.name,
            "restaurant_address": order.restaurant.address,
            "restaurant_coords": {
                "lat": -6.8235,  # Dar es Salaam coordinates
                "lng": 39.2695
            },
            "total_amount": order.total_amount,
            "items_count": len(order.items),
            "created_at": order.created_at.strftime('%I:%M %p')
        })
    
    return jsonify({
        "success": True,
        "orders": orders_data
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
        # Create admin user
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@msosihub.tz",
                password_hash=generate_password_hash("admin123"),
                first_name="System",
                last_name="Admin",
                phone="+255754327890",
                user_type="admin",
                address="Dar es Salaam, Tanzania"
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin / admin123")
        
        print("\n🚀 MsosiHub Started!")
        print("=" * 50)
        print("🏠 Home: http://localhost:5000/")
        print("🔑 Admin: admin / admin123")
        print("📧 Email: " + ("✅ Enabled" if EMAIL_ENABLED else "⚠️ Disabled"))
        print("=" * 50)
    
    app.run(debug=True, host="0.0.0.0", port=5000)