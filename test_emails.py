#!/usr/bin/env python3
"""
MsosiHub Email Testing Script
Test and configure email notifications for the MsosiHub platform
"""

import os
import sys
from notifications import EmailNotificationService, send_notification

def test_email_config():
    print("🧪 Testing Email Configuration")
    
    # Check environment variables
    email_user = os.environ.get('EMAIL_USER', 'msosihub@gmail.com')
    email_password = os.environ.get('EMAIL_PASSWORD', 'your-app-password')
    
    print(f"Email: {email_user}")
    print(f"Password: {'*' * len(email_password) if email_password != 'your-app-password' else 'NOT SET'}")
    
    if email_password == 'your-app-password':
        print("\n⚠️  To enable emails, set EMAIL_PASSWORD environment variable")
        print("For Gmail: Enable 2FA and generate App Password")
        return False
    
    # Test welcome email
    test_email = input("Enter test email: ").strip()
    if test_email:
        email_service = EmailNotificationService()
        result = email_service.send_welcome_email(test_email, "Test User")
        if result['success']:
            print("✅ Test email sent!")
        else:
            print(f"❌ Failed: {result.get('error')}")
    
    return True

def configure_email_settings():
    """Interactive email configuration"""
    print("⚙️  MsosiHub Email Configuration")
    print("=" * 50)
    
    print("\nTo enable email notifications, you need to configure your email settings.")
    print("\nFor Gmail (recommended):")
    print("1. Use your Gmail address")
    print("2. Enable 2-factor authentication")
    print("3. Generate an App Password")
    print("4. Use the App Password (not your regular password)")
    
    print("\nFor other email providers:")
    print("- Check your provider's SMTP settings")
    print("- Use appropriate port (587 for TLS, 465 for SSL)")
    
    print("\nEnvironment Variables to set:")
    print("export EMAIL_USER=your-email@gmail.com")
    print("export EMAIL_PASSWORD=your-app-password")
    print("export SMTP_SERVER=smtp.gmail.com")
    print("export SMTP_PORT=587")
    
    print("\nOr create a .env file in the msosihub directory:")
    print("EMAIL_USER=your-email@gmail.com")
    print("EMAIL_PASSWORD=your-app-password")
    print("SMTP_SERVER=smtp.gmail.com")
    print("SMTP_PORT=587")

def test_all_email_templates():
    """Test all email templates"""
    print("📧 Testing All Email Templates")
    print("=" * 50)
    
    test_email = input("📧 Enter test email address: ").strip()
    if not test_email:
        print("❌ No email address provided. Test cancelled.")
        return
    
    email_service = EmailNotificationService()
    
    # Test data
    test_order = {
        'id': 12345,
        'subtotal': 25000,
        'total': 27000,
        'delivery_address': '123 Test Street, Dar es Salaam',
        'phone': '+255 754 123 456'
    }
    
    test_items = [
        {'name': 'Grilled Chicken Salad', 'quantity': 2, 'price': 8000, 'total': 16000},
        {'name': 'Quinoa Bowl', 'quantity': 1, 'price': 9000, 'total': 9000}
    ]
    
    test_restaurant = {
        'name': 'Healthy Bites Restaurant'
    }
    
    templates_to_test = [
        ('welcome', 'Welcome Email', lambda: email_service.send_welcome_email(test_email, "Test User")),
        ('order_confirmation', 'Order Confirmation', lambda: email_service.send_order_confirmation(
            test_email, "Test Customer", test_order, test_items, test_restaurant)),
        ('order_status_update', 'Order Status Update', lambda: email_service.send_order_status_update(
            test_email, "Test Customer", 12345, "confirmed")),
        ('wallet_recharge', 'Wallet Recharge', lambda: email_service.send_wallet_recharge_notification(
            test_email, "Test Customer", 50000, 75000)),
        ('restaurant_welcome', 'Restaurant Welcome', lambda: email_service.send_restaurant_welcome(
            test_email, "Test Restaurant")),
        ('new_order_restaurant', 'New Order to Restaurant', lambda: email_service.send_new_order_to_restaurant(
            test_email, "Test Customer", test_order, test_items))
    ]
    
    for template_name, description, test_func in templates_to_test:
        print(f"\n📤 Testing {description}...")
        try:
            result = test_func()
            if result['success']:
                print(f"✅ {description} sent successfully!")
            else:
                print(f"❌ {description} failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ {description} error: {str(e)}")

def main():
    """Main function"""
    print("🌱 MsosiHub Email Testing & Configuration")
    print("=" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. Test email configuration")
        print("2. Configure email settings")
        print("3. Test all email templates")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            test_email_config()
        elif choice == '2':
            configure_email_settings()
        elif choice == '3':
            test_all_email_templates()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
