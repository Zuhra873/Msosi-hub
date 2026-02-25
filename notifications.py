#!/usr/bin/env python3
"""
MsosiHub Email Notification System
Handles all email notifications for customers, restaurants, drivers, and admins
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
from flask import current_app

class EmailNotificationService:
    def __init__(self):
        # Email configuration - can be set via environment variables
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.email_user = os.environ.get('EMAIL_USER', 'msosihub@gmail.com')
        self.email_password = os.environ.get('EMAIL_PASSWORD', 'your-app-password')
        self.from_name = "MsosiHub Tanzania"
        
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send HTML email with fallback text content"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.email_user}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text version if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully to {to_email}: {subject}")
            return {'success': True, 'message': 'Email sent successfully'}
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_email_template(self, template_type, **kwargs):
        """Generate HTML email templates"""
        
        # Common header and footer
        header = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>MsosiHub - {kwargs.get('title', 'Notification')}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                .header {{ background: linear-gradient(135deg, #2C5F41 0%, #21AC78 100%); color: white; padding: 30px 20px; text-align: center; }}
                .content {{ padding: 30px 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #21AC78; color: white; text-decoration: none; border-radius: 25px; font-weight: bold; }}
                .btn:hover {{ background-color: #2C5F41; }}
                .order-summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .status-badge {{ display: inline-block; padding: 5px 15px; border-radius: 15px; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
                .status-confirmed {{ background-color: #d4edda; color: #155724; }}
                .status-preparing {{ background-color: #cce7ff; color: #004085; }}
                .status-ready {{ background-color: #d1ecf1; color: #0c5460; }}
                .status-delivered {{ background-color: #d4edda; color: #155724; }}
                .highlight {{ background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌱 MsosiHub</h1>
                    <p>Tanzania's Healthy Food Delivery</p>
                </div>
                <div class="content">
        """
        
        footer = f"""
                </div>
                <div class="footer">
                    <p><strong>MsosiHub Tanzania</strong></p>
                    <p>📍 Dar es Salaam, Tanzania | 📞 +255 754 327 890</p>
                    <p>🌐 <a href="http://localhost:5000" style="color: #21AC78;">Visit MsosiHub</a></p>
                    <p style="font-size: 12px; margin-top: 20px;">
                        This email was sent to you because you have an account with MsosiHub.<br>
                        If you didn't expect this email, please contact us immediately.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Template content based on type
        if template_type == 'welcome':
            content = f"""
                <h2>Welcome to MsosiHub! 🎉</h2>
                <p>Dear {kwargs.get('name', 'Valued Customer')},</p>
                <p>Thank you for joining MsosiHub, Tanzania's premier healthy food delivery platform!</p>
                
                <div class="highlight">
                    <h3>🎁 Welcome Bonus: TZS 50,000</h3>
                    <p>We've added TZS 50,000 to your wallet to get you started on your healthy eating journey!</p>
                </div>
                
                <h3>What's Next?</h3>
                <ul>
                    <li>🍽️ Browse our healthy restaurants</li>
                    <li>🥗 Order nutritious meals</li>
                    <li>🚚 Get fresh food delivered in 30 minutes</li>
                    <li>💰 Use your prepaid wallet for easy payments</li>
                </ul>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/restaurants" class="btn">Start Ordering Healthy Food</a>
                </p>
                
                <p>Stay healthy, stay happy!</p>
                <p><strong>The MsosiHub Team</strong></p>
            """
            
        elif template_type == 'order_confirmation':
            order = kwargs.get('order')
            items = kwargs.get('items', [])
            restaurant = kwargs.get('restaurant')
            
            items_html = ""
            for item in items:
                items_html += f"""
                    <tr>
                        <td>{item['name']}</td>
                        <td style="text-align: center;">{item['quantity']}</td>
                        <td style="text-align: right;">TZS {item['price']:,.0f}</td>
                        <td style="text-align: right; font-weight: bold;">TZS {item['total']:,.0f}</td>
                    </tr>
                """
            
            content = f"""
                <h2>Order Confirmed! 🎉</h2>
                <p>Dear {kwargs.get('customer_name')},</p>
                <p>Your healthy meal order has been confirmed and is being prepared with care.</p>
                
                <div class="order-summary">
                    <h3>Order #{order['id']}</h3>
                    <p><strong>Restaurant:</strong> {restaurant['name']}</p>
                    <p><strong>Estimated Delivery:</strong> 25-30 minutes</p>
                    <p><strong>Status:</strong> <span class="status-badge status-confirmed">Confirmed</span></p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background-color: #e9ecef;">
                                <th style="padding: 10px; text-align: left;">Item</th>
                                <th style="padding: 10px; text-align: center;">Qty</th>
                                <th style="padding: 10px; text-align: right;">Price</th>
                                <th style="padding: 10px; text-align: right;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <div style="text-align: right; border-top: 2px solid #21AC78; padding-top: 10px;">
                        <p><strong>Subtotal: TZS {order['subtotal']:,.0f}</strong></p>
                        <p><strong>Delivery Fee: TZS 2,000</strong></p>
                        <p style="font-size: 18px; color: #21AC78;"><strong>Total Paid: TZS {order['total']:,.0f}</strong></p>
                    </div>
                </div>
                
                <div class="highlight">
                    <h4>📍 Delivery Details</h4>
                    <p><strong>Address:</strong> {order['delivery_address']}</p>
                    <p><strong>Phone:</strong> {order['phone']}</p>
                </div>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/my_orders" class="btn">Track Your Order</a>
                </p>
                
                <p>Thank you for choosing healthy eating with MsosiHub!</p>
            """
            
        elif template_type == 'order_status_update':
            order_id = kwargs.get('order_id')
            status = kwargs.get('status')
            customer_name = kwargs.get('customer_name')
            
            status_messages = {
                'confirmed': ('Order Confirmed! 👨‍🍳', 'Your order has been confirmed and the restaurant is preparing your healthy meal.'),
                'preparing': ('Cooking in Progress! 🔥', 'Your delicious healthy meal is being freshly prepared by our chef.'),
                'ready': ('Order Ready! ✅', 'Your order is ready and waiting for our delivery driver to pick it up.'),
                'out_for_delivery': ('On the Way! 🏍️', 'Your healthy meal is out for delivery and will arrive soon!'),
                'delivered': ('Delivered! 🎉', 'Your order has been delivered. Enjoy your healthy meal!')
            }
            
            title, message = status_messages.get(status, ('Order Updated', 'Your order status has been updated.'))
            
            content = f"""
                <h2>{title}</h2>
                <p>Dear {customer_name},</p>
                <p>{message}</p>
                
                <div class="order-summary">
                    <h3>Order #{order_id}</h3>
                    <p><strong>Status:</strong> <span class="status-badge status-{status}">{status.replace('_', ' ').title()}</span></p>
                    <p><strong>Updated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                {"<p>🍽️ <strong>Enjoy your healthy meal and thank you for choosing MsosiHub!</strong></p>" if status == 'delivered' else ""}
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/my_orders" class="btn">View Order Details</a>
                </p>
            """
            
        elif template_type == 'wallet_recharge':
            content = f"""
                <h2>Wallet Recharged! 💰</h2>
                <p>Dear {kwargs.get('customer_name')},</p>
                <p>Your MsosiHub wallet has been successfully recharged.</p>
                
                <div class="order-summary">
                    <h3>Recharge Details</h3>
                    <p><strong>Amount Added:</strong> TZS {kwargs.get('amount'):,.0f}</p>
                    <p><strong>New Balance:</strong> TZS {kwargs.get('new_balance'):,.0f}</p>
                    <p><strong>Payment Method:</strong> {kwargs.get('payment_method', 'Mobile Money')}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>You're all set to order more healthy meals!</p>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/restaurants" class="btn">Order Healthy Food</a>
                </p>
            """
            
        elif template_type == 'restaurant_welcome':
            content = f"""
                <h2>Welcome to MsosiHub Partner Network! 🏪</h2>
                <p>Dear {kwargs.get('restaurant_name')} Team,</p>
                <p>Congratulations! Your restaurant has been successfully registered with MsosiHub.</p>
                
                <div class="highlight">
                    <h3>🎯 Your Mission: Serve Healthy Tanzania</h3>
                    <p>Join us in promoting healthy eating across Tanzania by offering nutritious, fresh, and delicious meals.</p>
                </div>
                
                <h3>Getting Started:</h3>
                <ol>
                    <li>📝 Complete your restaurant profile</li>
                    <li>🍽️ Add your healthy menu items</li>
                    <li>📸 Upload appetizing photos</li>
                    <li>🚀 Start receiving orders!</li>
                </ol>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/restaurant_dashboard" class="btn">Access Restaurant Dashboard</a>
                </p>
                
                <p>Welcome to the MsosiHub family!</p>
                <p><strong>The MsosiHub Team</strong></p>
            """
            
        elif template_type == 'driver_welcome':
            content = f"""
                <h2>Welcome to MsosiHub Delivery Team! 🏍️</h2>
                <p>Dear {kwargs.get('name', 'Valued Driver')},</p>
                <p>Congratulations! You've joined MsosiHub as a delivery driver and are now part of our mission to deliver healthy food across Tanzania!</p>
                
                <div class="highlight">
                    <h3>🚚 Your Mission: Deliver Healthy Meals</h3>
                    <p>Help us connect healthy restaurants with customers by providing fast, reliable, and safe food delivery services.</p>
                </div>
                
                <h3>Getting Started:</h3>
                <ol>
                    <li>📱 Access your driver dashboard</li>
                    <li>🗺️ View available delivery orders</li>
                    <li>✅ Accept deliveries in your area</li>
                    <li>💰 Start earning from each delivery</li>
                </ol>
                
                <div class="order-summary">
                    <h3>💰 Earnings Structure</h3>
                    <ul>
                        <li><strong>Base Delivery Fee:</strong> TZS 3,000 per delivery</li>
                        <li><strong>Distance Bonus:</strong> Additional TZS 500 per km</li>
                        <li><strong>Customer Tips:</strong> 100% of tips go to you</li>
                        <li><strong>Weekly Payouts:</strong> Every Friday</li>
                    </ul>
                </div>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/driver_dashboard" class="btn">Access Driver Dashboard</a>
                </p>
                
                <p>Welcome to the MsosiHub delivery family!</p>
                <p><strong>The MsosiHub Team</strong></p>
            """
            
        elif template_type == 'new_order_restaurant':
            order = kwargs.get('order')
            items = kwargs.get('items', [])
            
            items_html = ""
            for item in items:
                items_html += f"<li>{item['quantity']}x {item['name']} - TZS {item['total']:,.0f}</li>"
            
            content = f"""
                <h2>New Order Received! 📝</h2>
                <p>Dear Restaurant Team,</p>
                <p>You have received a new healthy meal order that needs preparation.</p>
                
                <div class="order-summary">
                    <h3>Order #{order['id']}</h3>
                    <p><strong>Customer:</strong> {kwargs.get('customer_name')}</p>
                    <p><strong>Phone:</strong> {order['phone']}</p>
                    <p><strong>Order Time:</strong> {datetime.now().strftime('%I:%M %p')}</p>
                    <p><strong>Target Prep Time:</strong> 25-30 minutes</p>
                    
                    <h4>Items to Prepare:</h4>
                    <ul>{items_html}</ul>
                    
                    <p style="font-size: 18px; color: #21AC78;"><strong>Total: TZS {order['total']:,.0f}</strong></p>
                </div>
                
                <div class="highlight">
                    <p><strong>Special Instructions:</strong> {order.get('special_instructions', 'None')}</p>
                </div>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/restaurant_dashboard" class="btn">Manage Order</a>
                </p>
                
                <p>Please confirm and start preparation as soon as possible!</p>
            """
            
        else:
            content = f"""
                <h2>MsosiHub Notification</h2>
                <p>You have received a notification from MsosiHub.</p>
                <p>{kwargs.get('message', 'No message provided.')}</p>
            """
        
        return header + content + footer
    
    # Specific notification methods
    def send_welcome_email(self, user_email, user_name):
        """Send welcome email to new users"""
        subject = "Welcome to MsosiHub - Your Healthy Food Journey Starts Now! 🌱"
        html_content = self.get_email_template('welcome', name=user_name, title='Welcome')
        return self.send_email(user_email, subject, html_content)
    
    def send_order_confirmation(self, user_email, customer_name, order_data, items_data, restaurant_data):
        """Send order confirmation email"""
        subject = f"Order #{order_data['id']} Confirmed - MsosiHub"
        html_content = self.get_email_template(
            'order_confirmation',
            customer_name=customer_name,
            order=order_data,
            items=items_data,
            restaurant=restaurant_data,
            title='Order Confirmation'
        )
        return self.send_email(user_email, subject, html_content)
    
    def send_order_status_update(self, user_email, customer_name, order_id, status):
        """Send order status update email"""
        status_subjects = {
            'confirmed': f"Order #{order_id} Confirmed - Being Prepared! 👨‍🍳",
            'preparing': f"Order #{order_id} - Cooking in Progress! 🔥",
            'ready': f"Order #{order_id} Ready - Driver on the way! ✅",
            'out_for_delivery': f"Order #{order_id} Out for Delivery! 🏍️",
            'delivered': f"Order #{order_id} Delivered - Enjoy! 🎉"
        }
        
        subject = status_subjects.get(status, f"Order #{order_id} Status Update")
        html_content = self.get_email_template(
            'order_status_update',
            customer_name=customer_name,
            order_id=order_id,
            status=status,
            title='Order Update'
        )
        return self.send_email(user_email, subject, html_content)
    
    def send_wallet_recharge_notification(self, user_email, customer_name, amount, new_balance, payment_method='Mobile Money'):
        """Send wallet recharge confirmation"""
        subject = f"Wallet Recharged - TZS {amount:,.0f} Added Successfully 💰"
        html_content = self.get_email_template(
            'wallet_recharge',
            customer_name=customer_name,
            amount=amount,
            new_balance=new_balance,
            payment_method=payment_method,
            title='Wallet Recharge'
        )
        return self.send_email(user_email, subject, html_content)
    
    def send_restaurant_welcome(self, restaurant_email, restaurant_name):
        """Send welcome email to new restaurant partners"""
        subject = "Welcome to MsosiHub Partner Network! 🏪"
        html_content = self.get_email_template(
            'restaurant_welcome',
            restaurant_name=restaurant_name,
            title='Restaurant Welcome'
        )
        return self.send_email(restaurant_email, subject, html_content)
    
    def send_driver_welcome(self, driver_email, driver_name):
        """Send welcome email to new delivery drivers"""
        subject = "Welcome to MsosiHub Delivery Team! 🏍️"
        html_content = self.get_email_template(
            'driver_welcome',
            name=driver_name,
            title='Driver Welcome'
        )
        return self.send_email(driver_email, subject, html_content)
    
    def send_new_order_to_restaurant(self, restaurant_email, customer_name, order_data, items_data):
        """Send new order notification to restaurant"""
        subject = f"New Order #{order_data['id']} - Prepare Now! 📝"
        html_content = self.get_email_template(
            'new_order_restaurant',
            customer_name=customer_name,
            order=order_data,
            items=items_data,
            title='New Order'
        )
        return self.send_email(restaurant_email, subject, html_content)

# Global instance
email_service = EmailNotificationService()

def send_notification(user_id, message, notification_type="info", email_data=None):
    """Enhanced notification function with email support"""
    print(f"📱 NOTIFICATION [{notification_type.upper()}] to User {user_id}: {message}")
    
    # If email_data is provided, send email notification
    if email_data:
        email_type = email_data.get('type')
        email_address = email_data.get('email')
        
        if email_type == 'welcome':
            return email_service.send_welcome_email(
                email_address, 
                email_data.get('name')
            )
        elif email_type == 'order_confirmation':
            return email_service.send_order_confirmation(
                email_address,
                email_data.get('customer_name'),
                email_data.get('order'),
                email_data.get('items'),
                email_data.get('restaurant')
            )
        elif email_type == 'order_status':
            return email_service.send_order_status_update(
                email_address,
                email_data.get('customer_name'),
                email_data.get('order_id'),
                email_data.get('status')
            )
        elif email_type == 'wallet_recharge':
            return email_service.send_wallet_recharge_notification(
                email_address,
                email_data.get('customer_name'),
                email_data.get('amount'),
                email_data.get('new_balance'),
                email_data.get('payment_method')
            )
        elif email_type == 'restaurant_welcome':
            return email_service.send_restaurant_welcome(
                email_address,
                email_data.get('restaurant_name')
            )
        elif email_type == 'driver_welcome':
            return email_service.send_driver_welcome(
                email_address,
                email_data.get('name')
            )
        elif email_type == 'new_order_restaurant':
            return email_service.send_new_order_to_restaurant(
                email_address,
                email_data.get('customer_name'),
                email_data.get('order'),
                email_data.get('items')
            )
    
    return {'success': True, 'message': 'Console notification sent'}