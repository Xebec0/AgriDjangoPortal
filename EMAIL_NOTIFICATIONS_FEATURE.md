# Email Notifications for Application Status Updates

## 📧 Overview

Applicants now receive **automated email notifications** whenever their application status changes. This feature ensures applicants are immediately informed about their application status via email, in addition to the existing in-app notifications.

---

## ✅ Implementation Locations

### 1. **Candidate Application Status Updates** (Staff Action)
**Location**: `core/views.py` - `update_candidate_status()` function (line ~1949)

**Trigger**: When staff members approve or reject a candidate's application

**Email Sent To**: The applicant (found via email or registration record)

**Email Types**:
- **✅ Approved**: Congratulatory email with next steps
- **❌ Rejected**: Rejection notification with contact information

---

### 2. **Registration Status Updates** (Staff Action)
**Location**: `core/views.py` - `update_registration_status()` function (line ~1916)

**Trigger**: When staff members update registration status (Approved/Rejected/Pending)

**Email Sent To**: The registered user

**Email Types**:
- **✅ Approved**: Registration approval confirmation
- **❌ Rejected**: Rejection notification
- **⏳ Pending**: Status change to pending review

---

### 3. **Auto-Approval on Application** (User Action)
**Location**: `core/views.py` - `apply_candidate()` function (line ~697)

**Trigger**: When a user successfully applies to a program (auto-approved)

**Email Sent To**: The applicant (logged-in user)

**Email Types**:
- **✅ Approved**: Immediate approval confirmation with program details

---

## 📋 Email Content

Each email includes:

✅ **Personalized greeting** (uses first name or username)  
✅ **Status update** (Approved/Rejected/Pending)  
✅ **Program details** (name, location, dates)  
✅ **Direct link** to view the application/registration  
✅ **Next steps** or action items  
✅ **Professional signature** from AgroStudies Team  

---

## 🔧 Technical Details

### Email Configuration

Emails are sent using Django's `send_mail()` function with:
- **From**: `settings.DEFAULT_FROM_EMAIL` (configured in `settings.py`)
- **Fail Silently**: `True` - Email failures won't break the application flow
- **Logging**: All email sends are logged for tracking

### Error Handling

```python
try:
    send_mail(...)
    logger.info(f"Email sent to {user.email}")
except Exception as e:
    logger.error(f"Failed to send email: {e}")
```

Emails fail gracefully - if email sending fails, the status update still succeeds and in-app notifications still work.

---

## 🧪 Testing Email Notifications

### Method 1: Using Real Email (Development)

1. **Configure email settings** in `.env`:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=AgroStudies <noreply@agrostudies.com>
```

2. **Create a test application**:
   - Register as a user
   - Apply to a program
   - Check your email for approval notification

3. **Test status changes**:
   - Log in as admin/staff
   - Go to candidate detail page
   - Click "Approve Application" or "Reject Application"
   - Applicant receives email notification

---

### Method 2: Using Console Backend (Development)

For testing without real email server, emails are printed to console:

**In `settings.py`** (already configured for DEBUG mode):
```python
if DEBUG and not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

When this is active, all emails appear in the console/terminal where the Django server is running.

---

### Method 3: Test Email Command

Use the built-in test command:

```bash
python manage.py test_email your-email@example.com
```

---

## 📊 Email Tracking

All email sends are logged with:
- **Success**: `INFO` level log with recipient email
- **Failure**: `ERROR` level log with error details

**View logs**:
```bash
tail -f logs/app.log
```

**Log examples**:
```
INFO Status update email sent to user@example.com for candidate 123
ERROR Failed to send email to user@example.com: SMTP connection failed
```

---

## 🎯 Use Cases

### Use Case 1: Staff Approves Application
1. Staff member reviews candidate application
2. Staff clicks "Approve Application" button
3. **System sends**:
   - ✅ In-app notification
   - ✅ Email notification to applicant
4. Applicant receives both notifications immediately

### Use Case 2: User Applies to Program
1. User completes application form
2. User submits application
3. Application is auto-approved
4. **System sends**:
   - ✅ In-app notification
   - ✅ Email notification to applicant
5. User receives confirmation email with program details

### Use Case 3: Staff Rejects Application
1. Staff member reviews candidate application
2. Staff clicks "Reject Application" button
3. **System sends**:
   - ✅ In-app notification (error type)
   - ✅ Email notification with contact info
4. Applicant can reach out for feedback

---

## 🔐 Security & Privacy

- ✅ Emails only sent to verified user emails
- ✅ No sensitive data exposed in emails
- ✅ Secure links to application pages (require login)
- ✅ SMTP connection uses TLS encryption
- ✅ Failed emails don't expose error details to users

---

## 🚀 Production Deployment

### Before Deploying:

1. **Set production email credentials**:
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=AgroStudies <noreply@yourdomain.com>
```

2. **Verify email sending**:
```bash
python manage.py test_email admin@yourdomain.com
```

3. **Monitor email logs** after deployment

4. **Consider email service providers**:
   - SendGrid (recommended for high volume)
   - AWS SES
   - Mailgun
   - Gmail SMTP (for low volume)

---

## 📝 Customization

### Customize Email Content

Edit email templates in `core/views.py`:

1. **Subject lines** (line ~1996, ~1935, ~858)
2. **Email body** text
3. **Sender name** in `settings.py` → `DEFAULT_FROM_EMAIL`

### Add More Notifications

To add email notifications for other events:

```python
try:
    subject = "Your subject"
    message = "Your email body"
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )
    logger.info(f"Email sent to {user.email}")
except Exception as e:
    logger.error(f"Failed to send email: {e}")
```

---

## 🐛 Troubleshooting

### Issue: Emails not being sent

**Check**:
1. Email credentials in `.env` are correct
2. Email backend is not set to console mode
3. Check logs for error messages
4. Verify SMTP server is reachable

### Issue: Emails going to spam

**Solutions**:
1. Use a reputable email service provider
2. Configure SPF/DKIM records for your domain
3. Use a professional "From" address
4. Avoid spam trigger words in subject/body

### Issue: Email template not rendering

**Check**:
1. String formatting is correct
2. All variables exist (request.user, candidate, program)
3. Check logs for Python errors

---

## ✅ Summary

Email notifications are now implemented at **3 key points**:

1. ✅ **Staff approves/rejects** candidate applications
2. ✅ **Staff updates** registration status
3. ✅ **User applies** to a program (auto-approved)

All notifications include:
- Personalized content
- Program details
- Direct application links
- Professional formatting

The system is **production-ready** and **fail-safe** - email failures won't break the application flow.

---

## 📞 Support

For issues or questions:
- Check logs: `logs/app.log`
- Test emails: `python manage.py test_email`
- Review this documentation

**Status**: ✅ **IMPLEMENTED AND TESTED**

