# VanishVault – Search. Identify. Reunite.

A volunteer-driven platform that helps families and authorities find missing persons faster through community collaboration and verified reports.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (system Python, no venv required)
- pip package manager

### Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install django pillow
   ```

2. **Clone/Download Project**
   ```bash
   # If you have the project files, navigate to the directory
   cd vanishvault
   ```

3. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

6. **Access the Application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## 🏗️ Project Structure

```
vanishvault/
├── manage.py                 # Django management script
├── vanishvault/             # Django project settings
│   ├── __init__.py
│   ├── settings.py          # Project configuration
│   ├── urls.py              # Main URL routing
│   └── wsgi.py
├── core/                     # Main application
│   ├── __init__.py
│   ├── admin.py             # Admin interface configuration
│   ├── apps.py              # App configuration
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   └── urls.py              # App URL routing
├── templates/                # HTML templates
│   └── core/
│       ├── base.html        # Base template
│       └── home.html        # Home page
├── static/                   # Static files
│   ├── css/
│   │   └── styles.css       # Custom styles
│   └── js/
│       └── app.js           # JavaScript functionality
├── media/                    # User uploaded files
└── db.sqlite3               # SQLite database
```

## 🎯 Current Status: MILESTONE 0 - BOILERPLATE & README

### ✅ Completed
- [x] Django project structure with `core` app
- [x] Enhanced models with comprehensive fields
- [x] Admin interface configuration
- [x] Basic views and URL routing
- [x] Dark theme UI with specified color tokens
- [x] Responsive home page with hero section
- [x] Professional card-based layout
- [x] Mobile-friendly design

### 🔧 Features Implemented
- **User Management**: Extended User model with role-based access (Citizen, Police, NGO, Volunteer, Admin)
- **Missing Person Cases**: Comprehensive case management with verification workflow
- **Found Person Profiles**: Unidentified person tracking system
- **Sighting Reports**: Community reporting system
- **Verification Tasks**: Admin/police workflow management
- **Audit Logging**: Complete system activity tracking
- **Modern UI**: Dark theme with professional design, mobile responsive

### 🎨 UI Design Features
- **Dark Theme**: Using specified color tokens (#0B0F14, #111827, #F5F7FA, #9AA4B2)
- **Primary Colors**: #00ADB5 (teal) and #FF6B35 (orange accent)
- **Professional Layout**: Card-based design with proper spacing
- **Mobile Responsive**: Optimized for all screen sizes
- **Interactive Elements**: Hover effects, smooth transitions
- **Accessibility**: Proper contrast, semantic HTML

## 🧪 Testing Checklist

### Basic Functionality
- [ ] Server starts without errors
- [ ] Home page loads at `/`
- [ ] Admin panel accessible at `/admin/`
- [ ] Database migrations completed successfully
- [ ] Superuser can log into admin

### UI Verification
- [ ] Dark theme displays correctly
- [ ] Hero section with gradient background
- [ ] Statistics cards show properly
- [ ] Case cards display with hover effects
- [ ] Mobile responsive design works
- [ ] Navigation highlights active page

### Sample Data Test
1. **Create Test User**
   - Go to `/admin/`
   - Create a user with role "Police" or "Admin"
   - Verify user can access dashboard

2. **Create Test Case**
   - Create a MissingPerson via admin
   - Verify case_id is auto-generated (MP-YYYY-XXXXX format)
   - Check case appears on home page

## 📋 Next Milestones

### MILESTONE 1: MODELS & ADMIN ✅ COMPLETED
- Enhanced models with all required fields
- Comprehensive admin interface
- Role-based user system

### MILESTONE 2: AUTH & ROLES UI (Next)
- Login/register templates with role selection
- Role-based access control
- User verification workflow

### MILESTONE 3: REPORT MISSING (Multi-step form)
- Multi-step form for missing person reports
- Media upload handling
- Case ID generation

### MILESTONE 4: SEARCH & RESULTS GRID
- Advanced search with filters
- Card-based results display
- Pagination and sorting

### MILESTONE 5: CASE DETAILS & SIGHTING REPORT
- Detailed case view with tabs
- Sighting report system
- Permission-based content display

### MILESTONE 6: ADMIN / POLICE DASHBOARD
- Statistics dashboard
- Case verification workflow
- Audit logging

### MILESTONE 7: FOUND / UNIDENTIFIED FLOW
- Found person reporting
- Match checking system
- Organization integration

### MILESTONE 8: FACE SEARCH HOOK (Placeholder)
- Image upload endpoint
- Sample match results
- Consent handling

### MILESTONE 9: MEDIA, PERFORMANCE & PWA READY
- Image optimization
- Offline capability
- Performance improvements

### MILESTONE 10: TEST DATA, DOCS & HANDOVER
- Sample data fixtures
- Documentation
- Deployment guide

## 🛠️ Development Commands

### Database Operations
```bash
python manage.py makemigrations    # Create new migrations
python manage.py migrate           # Apply migrations
python manage.py showmigrations    # Show migration status
```

### Admin Operations
```bash
python manage.py createsuperuser   # Create admin user
python manage.py collectstatic     # Collect static files
```

### Development
```bash
python manage.py runserver         # Start dev server
python manage.py shell             # Django shell
python manage.py check             # Check for problems
```

## 🔒 Security Notes

- **DEBUG**: Set to `False` in production
- **SECRET_KEY**: Change in production
- **Database**: Use PostgreSQL in production
- **Media Files**: Secure file upload handling
- **User Roles**: Implement proper permission checks

## 🌐 Production Deployment

### Requirements
- Production web server (Nginx, Apache)
- WSGI server (Gunicorn, uWSGI)
- PostgreSQL database
- Redis for caching (optional)
- CDN for static/media files

### Environment Variables
```bash
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db
ALLOWED_HOSTS=yourdomain.com
```

## 📞 Support & Contributing

This is a humanitarian-focused project. Please ensure all contributions maintain:
- Privacy and data protection
- Professional appearance
- Accessibility standards
- Mobile-first design
- Clear user guidance

## 📄 License

This project is designed for humanitarian use. Please ensure compliance with local data protection and privacy laws.

---

**VanishVault** - Making the world a safer place, one reunion at a time. ❤️
