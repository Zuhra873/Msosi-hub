# MsosiHub Email Configuration Guide

## Overview
MsosiHub includes a comprehensive email notification system that sends welcome emails to new users, order confirmations, status updates, and more.

## Current Email Features
✅ **Welcome Emails** - Sent to all new users upon registration
- Customers: Welcome with TZS 50,000 bonus info
- Restaurants: Partner network welcome with setup instructions  
- Drivers: Delivery team welcome with earnings structure

✅ **Order Notifications** - Order confirmations and status updates
✅ **Wallet Recharge** - Confirmation emails for wallet top-ups
✅ **Restaurant Notifications** - New order alerts to restaurants

## Email Configuration

### Option 1: Environment Variables (Recommended)
Set these environment variables before running the app:

```bash
# For Gmail (recommended)
export EMAIL_USER=your-email@gmail.com
export EMAIL_PASSWORD=your-app-password
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587

# For other providers
export EMAIL_USER=your-email@yourprovider.com
export EMAIL_PASSWORD=your-password
export SMTP_SERVER=smtp.yourprovider.com
export SMTP_PORT=587
```

### Option 2: .env File
Create a `.env` file in the `msosihub` directory:

```env
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## Gmail Setup (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Navigate to Security
3. Enable 2-Step Verification

### Step 2: Generate App Password
1. Go to Google Account settings
2. Navigate to Security → App passwords
3. Select "Mail" and "Other (Custom name)"
4. Name it "MsosiHub"
5. Copy the generated 16-character password
6. Use this password as your `EMAIL_PASSWORD`

### Step 3: Test Configuration
Run the email test script:

```bash
cd msosihub
python test_emails.py
```

## Email Templates

The system includes professionally designed HTML email templates:

- **Welcome Email**: Personalized welcome with platform introduction
- **Restaurant Welcome**: Partner onboarding with setup instructions
- **Driver Welcome**: Delivery team welcome with earnings structure
- **Order Confirmation**: Detailed order summary with restaurant info
- **Status Updates**: Real-time order status notifications
- **Wallet Recharge**: Payment confirmation with new balance

## Testing Email Functionality

### Test Registration Emails
1. Configure email settings (see above)
2. Register a new user account
3. Check the registered email for welcome message

### Test All Email Types
```bash
python test_emails.py
```

### Manual Testing
```python
from notifications import EmailNotificationService

email_service = EmailNotificationService()
result = email_service.send_welcome_email("test@example.com", "Test User")
print(result)
```

## Troubleshooting

### Common Issues

**"Email password not configured"**
- Set the EMAIL_PASSWORD environment variable
- For Gmail, use an App Password (not your regular password)

**"Authentication failed"**
- Check your email and password
- For Gmail, ensure 2FA is enabled and you're using an App Password
- Check if your email provider allows SMTP access

**"Connection timeout"**
- Verify SMTP server and port settings
- Check your internet connection
- Some networks block SMTP ports

### Debug Mode
Enable debug logging by setting:
```bash
export FLASK_DEBUG=1
```

## Email Security

- ✅ Uses TLS encryption (port 587)
- ✅ App passwords for Gmail (more secure than regular passwords)
- ✅ Environment variables for sensitive data
- ✅ No hardcoded credentials

## Production Deployment

For production deployment:

1. Use a dedicated email service (SendGrid, Mailgun, etc.)
2. Set up proper DNS records (SPF, DKIM, DMARC)
3. Monitor email delivery rates
4. Implement email queuing for high volume

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your email configuration
3. Test with the provided test script
4. Check your email provider's SMTP settings

---

**Note**: Email functionality is optional. The app will work without email configuration, but users won't receive welcome emails or notifications. 