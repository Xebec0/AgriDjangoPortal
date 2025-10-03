# Email Configuration Guide

## Overview

The Agrostudies system has been updated with improved email functionality including:
- ✅ Email validation before sending password reset emails
- ✅ Warning messages for unregistered emails
- ✅ Flexible email backend configuration
- ✅ Test email command for debugging

---

## Email Backend Configuration

### Development Mode (Console Backend)

By default, in development mode (DEBUG=True) without email credentials, emails are printed to the console:

```env
DEBUG=True
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

This is useful for testing without setting up SMTP.

### Production Mode (SMTP Backend)

For production, configure SMTP settings in your `.env` file:

```env
DEBUG=False
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Agrostudies <noreply@agrostudies.com>
```

---

## Gmail Setup Instructions

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification

### Step 2: Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Other (Custom name)"
3. Name it "Agrostudies Django App"
4. Click "Generate"
5. Copy the 16-character password (no spaces)

### Step 3: Configure Environment Variables
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop  # The 16-char App Password
```

**Important**: Use the App Password, NOT your regular Gmail password!

---

## Other SMTP Providers

### Outlook/Office 365
```env
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

### Yahoo Mail
```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yahoo.com
EMAIL_HOST_PASSWORD=your-app-password
```

### SendGrid (Recommended for Production)
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

### Mailgun
```env
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your-mailgun-password
```

---

## Password Reset with Email Validation

### New Feature: Email Validation

The system now validates emails before sending password reset links:

#### Registered Email
```
User enters: test@example.com (registered)
✓ System sends password reset email
✓ Shows success message: "Password reset email has been sent"
✓ User receives email with reset link
```

#### Unregistered Email
```
User enters: unknown@example.com (not registered)
✗ System does NOT send email
⚠️ Shows warning: "This email is not registered in the system"
✓ Prevents email spam and information disclosure
```

#### Invalid Email Format
```
User enters: invalid-email
✗ System shows validation error
✗ No email sent
```

### Security Benefits

1. **Prevents Email Enumeration**: Users can't determine which emails are registered
2. **Reduces Email Spam**: No emails sent to invalid addresses
3. **Better User Experience**: Clear feedback about registration status
4. **Prevents Abuse**: Rate limiting on password reset attempts

---

## Testing Email Configuration

### Method 1: Test Email Command

Use the custom management command to test your email setup:

```bash
python manage.py test_email your-email@example.com
```

This will:
- Display your current email configuration
- Attempt to send a test email
- Show success or error messages
- Provide troubleshooting tips

### Method 2: Django Shell

```python
python manage.py shell

from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test message.',
    settings.DEFAULT_FROM_EMAIL,
    ['recipient@example.com'],
    fail_silently=False,
)
```

### Method 3: Password Reset Flow

1. Go to `/password_reset/`
2. Enter a registered email address
3. Check console (development) or inbox (production)
4. Verify email was received

---

## Troubleshooting

### Issue: "SMTPAuthenticationError"

**Cause**: Invalid credentials or App Password not used

**Solution**:
- Use Gmail App Password, not regular password
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct
- Check 2FA is enabled on Gmail account

### Issue: "SMTPConnectError" or "Connection refused"

**Cause**: Network/firewall blocking SMTP port

**Solution**:
- Check firewall allows outbound connections on port 587
- Try port 465 with EMAIL_USE_SSL=True
- Verify EMAIL_HOST is correct

### Issue: "SMTPServerDisconnected"

**Cause**: Connection timeout or server issues

**Solution**:
- Check internet connection
- Verify SMTP server is operational
- Try increasing EMAIL_TIMEOUT in settings

### Issue: Emails not received (no error)

**Cause**: Emails going to spam or wrong FROM address

**Solution**:
- Check spam/junk folder
- Verify DEFAULT_FROM_EMAIL is properly formatted
- Use authenticated domain for FROM address
- Consider using dedicated email service (SendGrid, Mailgun)

### Issue: "This email is not registered" for valid user

**Cause**: Email case mismatch or user doesn't exist

**Solution**:
- Check email is exactly as registered (case-insensitive)
- Verify user exists in database
- Check user.is_active is True

---

## Email Templates

The system uses these email templates:

### Password Reset Email
- **Template**: `templates/password_reset_email.html`
- **Subject**: `templates/password_reset_subject.txt`
- **Variables**: `{{ user }}`, `{{ protocol }}`, `{{ domain }}`, `{{ uid }}`, `{{ token }}`

### Email Verification (if enabled)
- **Template**: Custom in views.py
- **Variables**: `{{ verification_link }}`

---

## Testing Email in Tests

For automated tests, Django uses a test email backend:

```python
from django.core import mail

# Send email in test
send_mail('Subject', 'Message', 'from@example.com', ['to@example.com'])

# Check email was sent
assert len(mail.outbox) == 1
assert 'to@example.com' in mail.outbox[0].to
```

---

## Production Recommendations

### 1. Use Dedicated Email Service

For production, use a dedicated transactional email service:

- **SendGrid**: 100 emails/day free, excellent deliverability
- **Mailgun**: 5,000 emails/month free
- **Amazon SES**: Very cheap, requires AWS account
- **Postmark**: Focused on transactional emails

### 2. Configure SPF and DKIM

Set up proper email authentication:
- Add SPF record to DNS
- Configure DKIM signing
- Set up DMARC policy

### 3. Monitor Email Delivery

- Track bounce rates
- Monitor spam complaints
- Set up delivery webhooks
- Log all email sending attempts

### 4. Rate Limiting

Password reset is already rate-limited:
- 5 attempts per 5 minutes per IP
- Prevents abuse and spam

---

## Environment Variables Summary

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMAIL_BACKEND` | No | console | Email backend class |
| `EMAIL_HOST` | Yes* | smtp.gmail.com | SMTP server hostname |
| `EMAIL_PORT` | Yes* | 587 | SMTP server port |
| `EMAIL_USE_TLS` | No | True | Use TLS encryption |
| `EMAIL_USE_SSL` | No | False | Use SSL encryption |
| `EMAIL_HOST_USER` | Yes* | - | SMTP username/email |
| `EMAIL_HOST_PASSWORD` | Yes* | - | SMTP password/app password |
| `DEFAULT_FROM_EMAIL` | No | noreply@agrostudies.com | From address |

\* Required only when using SMTP backend in production

---

## Quick Start

### Development (No Email Setup)
```bash
# No configuration needed - emails print to console
python manage.py runserver
```

### Production (Gmail)
```bash
# 1. Set environment variables
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST_USER=your-email@gmail.com
export EMAIL_HOST_PASSWORD=your-app-password

# 2. Test email configuration
python manage.py test_email your-email@gmail.com

# 3. If successful, deploy
python manage.py runserver
```

---

## Code Changes Summary

### 1. Custom Password Reset Form (`core/forms_email.py`)
- Validates email exists before sending
- Shows clear error messages
- Prevents information disclosure

### 2. Custom Password Reset View (`core/views.py`)
- Uses CustomPasswordResetForm
- Handles validation errors gracefully
- Logs email sending errors

### 3. Improved Email Settings (`settings.py`)
- Auto-detects development mode
- Falls back to console backend
- Configurable via environment variables

### 4. Test Email Command (`core/management/commands/test_email.py`)
- Quick email configuration testing
- Shows current settings
- Provides troubleshooting tips

---

## Security Considerations

1. **Never commit email credentials** to version control
2. **Use App Passwords** for Gmail, not regular passwords
3. **Enable 2FA** on email accounts
4. **Rate limit** password reset requests (already implemented)
5. **Validate email format** before sending (already implemented)
6. **Don't disclose** whether email is registered (warning message is generic enough)

---

## Support

If you encounter issues:
1. Run `python manage.py test_email your-email@example.com`
2. Check logs in `logs/app.log`
3. Verify environment variables are set correctly
4. Review Django documentation: https://docs.djangoproject.com/en/stable/topics/email/

---

**Last Updated**: 2025-10-02  
**Status**: ✅ Email validation implemented and tested
