# Agrostudies Registration System for Farm Selection

A comprehensive Django-based web application for managing agricultural farm program registrations and candidate applications.

## 🌟 Features

- **User Authentication**: Secure registration, login, and profile management
- **Program Management**: Browse and search agricultural farm programs
- **Application System**: One-time application with automatic approval workflow
- **Document Management**: Upload and manage required documents (TOR, certificates, etc.)
- **Notifications**: Real-time notification system for application updates
- **Export Functionality**: Export candidate and registration data to CSV, Excel, and PDF
- **Admin Dashboard**: Comprehensive admin interface for staff management
- **Automated Backups**: Scheduled daily database backups
- **Activity Logging**: Complete audit trail of all system actions

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- PostgreSQL (for production) or SQLite (for development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AgriDjangoPortal
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and configure your settings
   # At minimum, set:
   # - SECRET_KEY (generate a secure random key)
   # - DEBUG=True (for development)
   # - DATABASE_URL (if using PostgreSQL)
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## 🧪 Running Tests

Run the test suite to ensure everything is working correctly:

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test core.tests.test_views

# Run with coverage report
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📁 Project Structure

```
AgriDjangoPortal/
├── agrostudies_project/     # Main project settings
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI configuration
├── core/                    # Main application
│   ├── management/          # Custom management commands
│   │   └── commands/
│   │       ├── backup_db.py
│   │       ├── createsu.py
│   │       └── scheduled_backup.py
│   ├── migrations/          # Database migrations
│   ├── tests/               # Test files
│   │   ├── test_views.py
│   │   ├── test_forms.py
│   │   └── test_models.py
│   ├── admin.py             # Admin configuration
│   ├── forms.py             # Form definitions
│   ├── models.py            # Database models
│   ├── urls.py              # App URL routing
│   └── views.py             # View functions
├── static/                  # Static files (CSS, JS, images)
├── templates/               # HTML templates
├── media/                   # User-uploaded files
├── logs/                    # Application logs
├── backups/                 # Database backups
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
└── manage.py                # Django management script
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

- `SECRET_KEY`: Django secret key (required)
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_URL`: Database connection string
- `EMAIL_HOST_USER`: SMTP email username
- `EMAIL_HOST_PASSWORD`: SMTP email password
- `ADMIN_REGISTRATION_CODE`: Code for admin registration

### Database Configuration

**Development (SQLite)**:
```env
DATABASE_URL=sqlite:///db.sqlite3
```

**Production (PostgreSQL)**:
```env
DATABASE_URL=postgresql://username:password@host:port/database_name
```

## 🚢 Deployment

### Deploying to Render

1. **Push code to GitHub**

2. **Create new Web Service on Render**
   - Connect your GitHub repository
   - Use the provided `render.yaml` configuration

3. **Set environment variables**
   - Configure all required environment variables in Render dashboard
   - Ensure `DEBUG=False` for production

4. **Deploy**
   - Render will automatically build and deploy your application
   - Migrations and superuser creation run automatically via `postDeployCommand`

### Manual Deployment

1. **Set production environment variables**
   ```bash
   export DEBUG=False
   export SECRET_KEY=<your-secret-key>
   export DATABASE_URL=<your-database-url>
   ```

2. **Run migrations**
   ```bash
   python manage.py migrate
   ```

3. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Start with Gunicorn**
   ```bash
   gunicorn agrostudies_project.wsgi:application
   ```

## 📊 Key Models

- **Profile**: Extended user information
- **AgricultureProgram**: Farm programs with capacity and requirements
- **Candidate**: Approved applications with full candidate details
- **Registration**: Legacy registration system
- **University**: Educational institutions
- **Notification**: User notification system
- **ActivityLog**: Audit trail for all actions

## 🔐 Security Features

- CSRF protection enabled
- Secure password hashing
- File upload validation (type and size)
- Staff-only access controls
- Production security headers (HSTS, XSS protection)
- Transaction-based capacity management to prevent race conditions
- Comprehensive activity logging

## 🛠️ Management Commands

```bash
# Create superuser (custom command)
python manage.py createsu

# Manual database backup
python manage.py backup_db

# Scheduled backup (runs automatically via cron)
python manage.py scheduled_backup
```

## 📝 API Endpoints

### Public Endpoints
- `/` - Home page
- `/programs/` - List all programs
- `/programs/<id>/` - Program details
- `/register/` - User registration
- `/login/` - User login

### Protected Endpoints (Login Required)
- `/profile/` - User profile
- `/candidates/` - Candidate list
- `/programs/<id>/apply/` - Apply to program
- `/notifications/` - User notifications

### Staff-Only Endpoints
- `/admin/` - Admin dashboard
- `/candidates/export/csv/` - Export candidates to CSV
- `/programs/<id>/registrants/` - View program registrants

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 👨‍💻 Developer

Developed by: Greyson Latosa

## 📞 Support

For support, please contact: support@agrostudies.com

## 🔄 Changelog

### Version 1.0.0 (Current)
- Initial release
- User authentication and profile management
- Program browsing and application system
- Document upload functionality
- Notification system
- Export to CSV, Excel, and PDF
- Automated backups
- Activity logging and audit trail
- Production-ready security features
- Comprehensive test coverage

## 🐛 Known Issues

None at this time. Please report any issues via the issue tracker.

## 🎯 Roadmap

- [ ] Add rate limiting for login attempts
- [ ] Implement email verification system
- [ ] Add multi-language support
- [ ] Create mobile-responsive dashboard
- [ ] Add real-time notifications via WebSockets
- [ ] Implement advanced search and filtering
- [ ] Add data analytics and reporting dashboard
