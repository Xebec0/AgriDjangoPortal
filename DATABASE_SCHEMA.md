# AgriDjangoPortal Database Schema

## Overview
This document describes the complete database schema for the AgriDjangoPortal application. The project uses Django ORM with SQLite (development) or PostgreSQL (production) as the database backend.

---

## Database Tables

### 1. **auth_user** (Django Built-in)
Core authentication table managed by Django.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment user ID |
| username | VARCHAR(150) | UNIQUE, NOT NULL | Unique username for login |
| first_name | VARCHAR(150) | | User's first name |
| last_name | VARCHAR(150) | | User's last name |
| email | VARCHAR(254) | | User's email address |
| password | VARCHAR(128) | NOT NULL | Hashed password |
| is_staff | BOOLEAN | DEFAULT FALSE | Can access admin panel |
| is_active | BOOLEAN | DEFAULT TRUE | Account is active |
| is_superuser | BOOLEAN | DEFAULT FALSE | Has all permissions |
| last_login | DATETIME | NULL | Last login timestamp |
| date_joined | DATETIME | NOT NULL | Account creation date |

---

### 2. **core_profile**
Extended user profile information with personal, educational, and document details.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGINT | PRIMARY KEY | Auto-increment ID |
| user_id | BIGINT | FOREIGN KEY (auth_user) | Reference to auth_user |
| bio | TEXT | | User biography |
| location | VARCHAR(100) | | Geographic location |
| date_joined | DATETIME | NOT NULL | Profile creation date |
| email_verified | BOOLEAN | DEFAULT FALSE | Email verification status |
| verification_token | VARCHAR(100) | NULL | Email verification token |
| profile_image | VARCHAR(100) | NULL | Profile image path (ImageField) |
| phone_number | VARCHAR(20) | NULL | Contact phone number |
| father_name | VARCHAR(100) | NULL | Father's name |
| mother_name | VARCHAR(100) | NULL | Mother's name |
| date_of_birth | DATE | NULL | Date of birth |
| country_of_birth | VARCHAR(100) | NULL | Birth country |
| nationality | VARCHAR(100) | NULL | Nationality |
| religion | VARCHAR(100) | NULL | Religious affiliation |
| gender | VARCHAR(10) | CHOICES: 'Male', 'Female' | Biological gender |
| has_international_license | BOOLEAN | DEFAULT FALSE | Has international driver's license |
| license_scan | VARCHAR(100) | NULL | License document path |
| address | TEXT | NULL | Residential address |
| passport_number | VARCHAR(20) | NULL | Passport number |
| passport_issue_date | DATE | NULL | Passport issue date |
| passport_expiry_date | DATE | NULL | Passport expiration date |
| place_of_issue | VARCHAR(100) | NULL | Passport issue location |
| highest_education_level | VARCHAR(20) | CHOICES: 'high_school', 'bachelor', 'master', 'phd', 'other' | Educational attainment |
| institution_name | VARCHAR(200) | NULL | Educational institution name |
| graduation_year | SMALLINT | NULL | Year of graduation |
| field_of_study | VARCHAR(100) | NULL | Major/Field of study |
| university_id | BIGINT | FOREIGN KEY (core_university) | Reference to university |
| specialization | VARCHAR(100) | NULL | Primary specialization |
| secondary_specialization | VARCHAR(100) | NULL | Secondary specialization |
| year_graduated | SMALLINT | NULL | Year of graduation (alternate field) |
| smokes | VARCHAR(10) | CHOICES: 'Never', 'Sometimes', 'Often' | Smoking habits |
| shoes_size | VARCHAR(10) | NULL | Shoe size |
| shirt_size | VARCHAR(10) | NULL | Shirt size |
| preferred_country | VARCHAR(100) | NULL | Preferred country for placement |
| willing_to_relocate | BOOLEAN | DEFAULT TRUE | Willing to relocate for programs |
| special_requirements | TEXT | NULL | Special accommodations needed |
| passport_scan | VARCHAR(100) | NULL | Passport document path |
| academic_certificate | VARCHAR(100) | NULL | Academic certificate path |
| tor | VARCHAR(100) | NULL | Transcript of Records path |
| nc2_tesda | VARCHAR(100) | NULL | NC2 from TESDA path |
| diploma | VARCHAR(100) | NULL | Diploma document path |
| good_moral | VARCHAR(100) | NULL | Good Moral Character certificate path |
| nbi_clearance | VARCHAR(100) | NULL | NBI Clearance document path |

**Relationships:**
- ONE-TO-ONE: `user_id` → `auth_user.id`
- MANY-TO-ONE: `university_id` → `core_university.id`

**Indexes:**
- `(user_id)` - UNIQUE

---

### 3. **core_university**
Educational institutions referenced by profiles.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGINT | PRIMARY KEY | Auto-increment ID |
| name | VARCHAR(200) | NOT NULL | University name |
| code | VARCHAR(20) | UNIQUE, NOT NULL | University code |
| country | VARCHAR(100) | NOT NULL | Country location |

---

### 4. **core_agricultureprogram**
Agricultural training programs offered by the platform.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGINT | PRIMARY KEY | Auto-increment ID |
| title | VARCHAR(200) | NOT NULL | Program name |
| description | TEXT | NOT NULL | Program description |
| start_date | DATE | NOT NULL | Program start date |
| country | VARCHAR(100) | NOT NULL | Program country |
| location | VARCHAR(100) | NOT NULL | Specific location |
| capacity | SMALLINT | NOT NULL | Maximum participants |
| registration_deadline | DATETIME | NULL | Application deadline |
| image | VARCHAR(100) | NULL | Program image path |
| is_featured | BOOLEAN | DEFAULT FALSE | Display on landing page |
| created_at | DATETIME | NOT NULL, AUTO | Creation timestamp |
| updated_at | DATETIME | NOT NULL, AUTO | Last update timestamp |
| required_gender | VARCHAR(10) | CHOICES: 'Any', 'Male', 'Female' | Gender requirement |
| requires_license | BOOLEAN | DEFAULT FALSE | International license required |

**Ordering:** `-is_featured, -created_at`

---

### 5. **core_registration**
User registrations for agriculture programs.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGINT | PRIMARY KEY | Auto-increment ID |
| user_id | BIGINT | FOREIGN KEY (auth_user) | Registering user |
| program_id | BIGINT | FOREIGN KEY (core_agricultureprogram) | Target program |
| registration_date | DATETIME | NOT NULL, AUTO | Registration timestamp |
| status | VARCHAR(10) | CHOICES: 'pending', 'approved', 'rejected' | Application status |
| notes | TEXT | | Admin notes on application |
| processed | BOOLEAN | DEFAULT FALSE | Converted to candidate |
| tor | VARCHAR(100) | NULL | Transcript of Records |
| nc2_tesda | VARCHAR(100) | NULL | NC2 from TESDA |
| diploma | VARCHAR(100) | NULL | Diploma |
| good_moral | VARCHAR(100) | NULL | Good Moral Character |
| nbi_clearance | VARCHAR(100) | NULL | NBI Clearance |

**Relationships:**
- MANY-TO-ONE: `user_id` → `auth_user.id`
- MANY-TO-ONE: `program_id` → `core_agricultureprogram.id`

**Constraints:**
- UNIQUE: `(user_id, program_id)` - Prevent duplicate registrations

**Indexes:**
- `(user_id)`
- `(program_id)`

---

### 6. **core_candidate**
Candidate profiles with comprehensive application data.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGINT | PRIMARY KEY | Auto-increment ID |
| passport_number | VARCHAR(20) | | Passport identifier |
| first_name | VARCHAR(100) | | Candidate first name |
| last_name | VARCHAR(100) | | Candidate last name |
| email | VARCHAR(254) | NULL | Email address |
| date_of_birth | DATE | NULL | Birth date |
| country_of_birth | VARCHAR(100) | | Birth country |
| nationality | VARCHAR(100) | | Citizenship |
| religion | VARCHAR(100) | NULL | Religious affiliation |
| father_name | VARCHAR(100) | NULL | Father's name |
| mother_name | VARCHAR(100) | NULL | Mother's name |
| passport_issue_date | DATE | NULL | Issue date |
| passport_expiry_date | DATE | NULL | Expiration date |
| gender | VARCHAR(10) | CHOICES: 'Male', 'Female', 'Other' | Gender |
| shoes_size | VARCHAR(10) | NULL | Shoe size |
| shirt_size | VARCHAR(10) | NULL | Shirt size |
| university_id | BIGINT | FOREIGN KEY (core_university) | University attended |
| year_graduated | SMALLINT | NULL | Graduation year |
| specialization | VARCHAR(100) | | Primary specialization |
| secondary_specialization | VARCHAR(100) | NULL | Secondary specialization |
| smokes | VARCHAR(10) | CHOICES: 'Never', 'Sometimes', 'Often' | Smoking status |
| program_id | BIGINT | FOREIGN KEY (core_agricultureprogram) | Associated program |
| status | VARCHAR(20) | CHOICES: 'Draft', 'New', 'Approved', 'Rejected' | Application status |
| created_at | DATETIME | NOT NULL, AUTO | Record creation |
| updated_at | DATETIME | NOT NULL, AUTO | Last update |
| profile_image | VARCHAR(100) | NULL | Candidate photo |
| license_scan | VARCHAR(100) | NULL | Driver's license |
| passport_scan | VARCHAR(100) | NULL | Passport scan |
| academic_certificate | VARCHAR(100) | NULL | Academic certificate |
| tor | VARCHAR(100) | NULL | Transcript of Records |
| nc2_tesda | VARCHAR(100) | NULL | NC2 from TESDA |
| diploma | VARCHAR(100) | NULL | Diploma |
| good_moral | VARCHAR(100) | NULL | Good Moral Character |
| nbi_clearance | VARCHAR(100) | NULL | NBI Clearance |
| created_by_id | BIGINT | FOREIGN KEY (auth_user) | Creator user |

**Relationships:**
- MANY-TO-ONE: `university_id` → `core_university.id`
- MANY-TO-ONE: `program_id` → `core_agricultureprogram.id`
- MANY-TO-ONE: `created_by_id` → `auth_user.id`

**Indexes:**
- `(program_id)`
- `(created_by_id)`

---

### 7. **core_notification**
User notification system for alerts and messages.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGINT | PRIMARY KEY | Auto-increment ID |
| user_id | BIGINT | FOREIGN KEY (auth_user) | Target user |
| message | TEXT | NOT NULL | Notification message |
| notification_type | VARCHAR(10) | CHOICES: 'info', 'success', 'warning', 'error' | Notification type |
| link | VARCHAR(255) | NULL | Associated URL link |
| created_at | DATETIME | NOT NULL, AUTO | Creation timestamp |
| read | BOOLEAN | DEFAULT FALSE | Read status |

**Relationships:**
- MANY-TO-ONE: `user_id` → `auth_user.id`

**Ordering:** `-created_at`

**Indexes:**
- `(user_id)`
- `(user_id, read)`
- `(created_at)`

---

### 8. **core_activitylog**
Comprehensive audit trail for all system actions.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGINT | PRIMARY KEY | Auto-increment ID |
| user_id | BIGINT | FOREIGN KEY (auth_user) | Acting user |
| action_type | VARCHAR(20) | CHOICES: 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'FAILED_LOGIN', 'SYSTEM' | Action type |
| model_name | VARCHAR(100) | NOT NULL, INDEXED | Model in 'app.Model' format |
| object_id | VARCHAR(64) | NULL | Instance ID being acted upon |
| before_data | JSON | NULL | Data before change |
| after_data | JSON | NULL | Data after change |
| ip_address | INET | NULL | Request IP address |
| session_key | VARCHAR(40) | NULL | Django session key |
| timestamp | DATETIME | NOT NULL, DEFAULT NOW | Action timestamp |

**Relationships:**
- MANY-TO-ONE: `user_id` → `auth_user.id` (SET NULL on user delete)

**Ordering:** `-timestamp`

**Indexes:**
- `(user_id)`
- `(action_type)`
- `(timestamp)`
- `(model_name)`

---

### 9. **core_uploadedfile**
Metadata and tracking for user file uploads.

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGINT | PRIMARY KEY | Auto-increment ID |
| user_id | BIGINT | FOREIGN KEY (auth_user), INDEXED | Uploading user |
| document_type | VARCHAR(50) | CHOICES: (9 document types), INDEXED | Document classification |
| file_name | VARCHAR(255) | NOT NULL | Original filename |
| file_path | VARCHAR(500) | NOT NULL | Storage path |
| file_size | BIGINT | NOT NULL | Size in bytes |
| file_hash | VARCHAR(64) | INDEXED, NOT NULL | SHA-256 hash |
| mime_type | VARCHAR(100) | NULL | Content type |
| model_name | VARCHAR(50) | NOT NULL | 'Profile', 'Registration', or 'Candidate' |
| model_id | BIGINT | NOT NULL | Instance ID |
| uploaded_at | DATETIME | NOT NULL, AUTO, INDEXED | Upload timestamp |
| updated_at | DATETIME | NOT NULL, AUTO | Last update |
| is_active | BOOLEAN | DEFAULT TRUE | File is current |

**Relationships:**
- MANY-TO-ONE: `user_id` → `auth_user.id`

**Constraints:**
- UNIQUE: `(user_id, document_type, file_hash)` - Prevent duplicate file uploads

**Ordering:** `-uploaded_at`

**Indexes:**
- `(user_id, document_type)`
- `(user_id, file_hash)`
- `(file_hash)`
- `(user_id, uploaded_at)`

**Document Types:**
- `profile_image` - Profile Image
- `license_scan` - License Scan
- `passport_scan` - Passport Scan
- `academic_certificate` - Academic Certificate
- `tor` - Transcript of Records (TOR)
- `nc2_tesda` - NC2 from TESDA
- `diploma` - Diploma
- `good_moral` - Good Moral Character
- `nbi_clearance` - NBI Clearance

---

## Data Models Relationships

```
auth_user (1)
    ├─── (1:1) core_profile
    ├─── (1:N) core_registration ──┐
    ├─── (1:N) core_candidate ─────┼──> core_agricultureprogram
    ├─── (1:N) core_notification   │
    ├─── (1:N) core_activitylog    │
    └─── (1:N) core_uploadedfile   │
              │                      │
              └──────────────────────┘

core_university (1)
    ├─── (1:N) core_profile
    └─── (1:N) core_candidate
```

---

## Key Features

### 1. **Flexible Application System**
- Candidates can apply with incomplete profiles (blank/null fields allowed)
- Status tracking: Draft → New → Approved/Rejected
- No strict unique constraints on passport_number and university

### 2. **File Management**
- SHA-256 hash-based duplicate detection
- Prevents same file from being uploaded multiple times
- Tracks file metadata for integrity verification
- Supports 9 document types with dedicated storage paths

### 3. **Audit Trail**
- Complete activity logging with before/after data snapshots
- Supports rollback functionality
- IP address and session tracking for security
- 7 action types: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, FAILED_LOGIN, SYSTEM

### 4. **Notification System**
- 4 notification types: info, success, warning, error
- Read/unread status tracking
- Optional link attachment for contextual navigation

### 5. **Registration & Approval Workflow**
- 3-status workflow: Pending → Approved/Rejected
- Unique constraint prevents duplicate program registrations
- Document upload during registration
- Processed flag for candidate conversion

---

## Storage Paths

All files uploaded through the application are stored under the `media/` directory with the following structure:

```
media/
├── profile_images/           # Profile photos
├── candidate_images/         # Candidate photos
├── candidate_licenses/       # Driver's licenses
├── candidate_certificates/   # Academic certificates
├── passports/               # Passport scans
├── licenses/                # License scans (alternate)
├── passport_scans/          # Passport scans (alternate)
├── documents/
│   ├── tor/                 # Transcripts of Records
│   ├── tesda/               # NC2 from TESDA
│   ├── diploma/             # Diplomas
│   ├── moral/               # Good Moral Character
│   └── nbi/                 # NBI Clearances
└── program_images/          # Program/Farm images
```

---

## Caching Strategy

Configured cache settings in settings.py:

| Resource | TTL | Backend |
|----------|-----|---------|
| Default | 5 min (300s) | Redis/LocMemCache |
| Programs | 10 min (600s) | Redis/LocMemCache |
| Candidates | 5 min (300s) | Redis/LocMemCache |
| User Data | 15 min (900s) | Redis/LocMemCache |
| Static Content | 1 hour (3600s) | WhiteNoise |

---

## Security Features

1. **Password Security:** Django password validators enforced
2. **SQL Injection:** Protected via Django ORM parameterized queries
3. **CSRF Protection:** Django CSRF middleware with trusted origins
4. **SSL/TLS:** HTTPS in production with HSTS headers
5. **Email Verification:** Token-based email verification
6. **Activity Audit:** Complete action logging with timestamps
7. **File Integrity:** SHA-256 hashing for duplicate detection
8. **Session Security:** Configurable session cookie security

---

## Performance Considerations

1. **Indexes:** Strategic indexing on frequently queried fields (user_id, timestamps, model_name)
2. **Database Connection:** 600s connection timeout with health checks
3. **Query Optimization:** Cachalot ORM automatic caching in production
4. **File Operations:** Chunk-based file hashing for memory efficiency
5. **Session Storage:** Redis for production, database for development

---

## Migration Strategy

The application uses Django migrations to track schema changes. New migrations are automatically created when models are modified:

```bash
python manage.py makemigrations
python manage.py migrate
```

All migrations are version-controlled in the `migrations/` folder of each app.

---

## Database Diagram (ER Format)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            DATABASE SCHEMA                              │
├─────────────────────────────────────────────────────────────────────────┤

auth_user PK: id
├── id (BIGINT)
├── username (VARCHAR-150, UNIQUE)
├── email (VARCHAR-254)
├── password (VARCHAR-128)
├── is_staff (BOOLEAN)
├── is_active (BOOLEAN)
├── is_superuser (BOOLEAN)
├── date_joined (DATETIME)

    1 ────── 1:1 ────────► core_profile PK: id
                           ├── id (BIGINT)
                           ├── user_id (FK: auth_user)
                           ├── bio (TEXT)
                           ├── email_verified (BOOLEAN)
                           ├── profile_image (VARCHAR)
                           ├── university_id (FK: core_university)
                           ├── [document fields...]
                           └── [personal fields...]

    1 ──────── 1:N ────────► core_registration PK: id
                            ├── id (BIGINT)
                            ├── user_id (FK: auth_user)
                            ├── program_id (FK: core_agricultureprogram)
                            ├── status (VARCHAR-10)
                            ├── processed (BOOLEAN)
                            └── [document fields...]

    1 ──────── 1:N ────────► core_candidate PK: id
                            ├── id (BIGINT)
                            ├── created_by_id (FK: auth_user)
                            ├── program_id (FK: core_agricultureprogram)
                            ├── university_id (FK: core_university)
                            ├── status (VARCHAR-20)
                            └── [profile & document fields...]

    1 ──────── 1:N ────────► core_notification PK: id
                            ├── id (BIGINT)
                            ├── user_id (FK: auth_user)
                            ├── message (TEXT)
                            ├── notification_type (VARCHAR-10)
                            └── read (BOOLEAN)

    1 ──────── 1:N ────────► core_activitylog PK: id
                            ├── id (BIGINT)
                            ├── user_id (FK: auth_user)
                            ├── action_type (VARCHAR-20)
                            ├── model_name (VARCHAR-100)
                            ├── before_data (JSON)
                            ├── after_data (JSON)
                            └── timestamp (DATETIME)

    1 ──────── 1:N ────────► core_uploadedfile PK: id
                            ├── id (BIGINT)
                            ├── user_id (FK: auth_user)
                            ├── document_type (VARCHAR-50)
                            ├── file_name (VARCHAR-255)
                            ├── file_hash (VARCHAR-64)
                            ├── model_name (VARCHAR-50)
                            └── is_active (BOOLEAN)

core_university PK: id
├── id (BIGINT)
├── name (VARCHAR-200)
├── code (VARCHAR-20, UNIQUE)
└── country (VARCHAR-100)

    1 ──────── 1:N ────────► core_profile
    1 ──────── 1:N ────────► core_candidate

core_agricultureprogram PK: id
├── id (BIGINT)
├── title (VARCHAR-200)
├── description (TEXT)
├── country (VARCHAR-100)
├── capacity (SMALLINT)
├── required_gender (VARCHAR-10)
└── [timestamps & image fields...]

    1 ──────── 1:N ────────► core_registration
    1 ──────── 1:N ────────► core_candidate

```

---

Generated: November 25, 2025
