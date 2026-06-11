# VanishVault System Flowchart & Access Control Documentation

## 🔄 **System Architecture Flowchart**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           VANISHVAULT SYSTEM                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PUBLIC        │    │   REGISTERED    │    │   VERIFIED      │
│   (Unauthenticated) │   │   USERS         │    │   USERS         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ • Browse Cases  │    │ • Report Cases  │    │ • Advanced      │
│ • Search        │    │ • Face Search   │    │   Search        │
│ • View Details  │    │ • Sighting Rep  │    │ • Verify Cases  │
│ • Register      │    │ • Contact Req   │    │ • Admin Panel   │
│ • Login         │    │ • Profile Mgmt  │    │ • Audit Logs    │
└─────────────────┘    └─────────────────┘    └─────────────────┘

🔄 USER REGISTRATION FLOW:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. Registration Form → 2. Role Selection → 3. Document Upload → 4. Email/Phone   │
│    Validation           Validation              Verification        Verification    │
│         │                       │                       │                   │
│         ▼                       ▼                       ▼                   ▼
│   [Citizen]              [Police/NGO]           [Auto-Verify]     [Admin Review]   │
│   Auto-Approved          Requires ID            Immediate         Manual Approval  │
│                         Document Upload         Access             Pending Status   │
└─────────────────────────────────────────────────────────────────────────────────┘

🔒 LOGIN & SECURITY FLOW:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. Login Attempt → 2. Rate Limit Check → 3. Account Lockout → 4. Authentication │
│    Username/Password    Failed Attempts      5 Attempts =      Credentials     │
│         │               Check (1hr)          30min Lockout      Validation       │
│         ▼                       │                       │                   │
│   [Success]              [Blocked]            [Locked]           [Success/Failed] │
│   Session Start          Rate Limited         Try Again Later   Log Event        │
│   Audit Log              Log Attempt          Log Event         Redirect/Error   │
└─────────────────────────────────────────────────────────────────────────────────┘

📊 CASE MANAGEMENT FLOW:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ MISSING PERSON CASE FLOW:                                                    │
│ Report → AI Face Matching → Admin Review → Verified → Public Search → Match →  │
│   │         │                    │            │              │        │      │
│   ▼         ▼                    ▼            ▼              ▼        ▼      │
│ Pending   Potential            Verification  Public      Found     Closed   │
│ Status   Matches               Required     Visible     Person    Case     │
└─────────────────────────────────────────────────────────────────────────────────┘

🤖 AI FACE MATCHING FLOW:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. Image Upload → 2. Preprocessing → 3. Face Detection → 4. Feature Extract  │
│    Photo/Sketch        Lighting         Multi-Angle     Embedding      │
│    Base64/File        Normalization     Detection       Generation     │
│         │                  │               │               │           │
│         ▼                  ▼               ▼               ▼           │
│ 5. Database Compare → 6. Confidence Score → 7. Classification → 8. Results   │
│    Missing/Found       High/Med/Low      Match/No Match   Ranked List  │
│    Persons             Percentage        Color Coded     API/Web UI  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 👥 **User Roles & Access Control Matrix**

### **🔓 PUBLIC (Unauthenticated Users)**
**Access Level**: Basic public information only

| Feature | Access | Description |
|---------|--------|-------------|
| Browse Home Page | ✅ | View platform overview |
| Search Missing Persons | ✅ | Basic search functionality |
| View Case Details | ✅ | Public information only |
| View Found Persons | ✅ | Unidentified persons list |
| Register Account | ✅ | Create new account |
| Login | ✅ | Access authentication |
| Report Sighting | ✅ | Anonymous reporting |
| Contact Request | ❌ | Requires login |
| Face Search | ❌ | Requires login |
| Report Cases | ❌ | Requires login |
| Admin Dashboard | ❌ | Admin only |

---

### **👤 CITIZEN (Verified by default)**
**Access Level**: Standard user functionality

| Feature | Access | Description |
|---------|--------|-------------|
| All Public Features | ✅ | Inherit all public access |
| Report Missing Person | ✅ | Create missing person reports |
| Report Found Person | ✅ | Report unidentified persons |
| Face Search | ✅ | AI-powered face matching |
| Advanced Search | ✅ | Filtered search options |
| Contact Reporters | ✅ | Request contact info |
| Profile Management | ✅ | Update personal info |
| Sighting Reports | ✅ | Report sightings |
| View Statistics | ✅ | Public statistics only |
| Verify Cases | ❌ | Police/Admin only |
| Admin Dashboard | ❌ | Admin only |
| User Management | ❌ | Admin only |
| Audit Logs | ❌ | Admin only |

---

### **👮 POLICE OFFICER (Requires Verification)**
**Access Level**: Law enforcement capabilities

| Feature | Access | Description |
|---------|--------|-------------|
| All Citizen Features | ✅ | Inherit all citizen access |
| Verify Cases | ✅ | Approve/reject reports |
| Access Dashboard | ✅ | Police-specific dashboard |
| View Full Case Details | ✅ | Sensitive information |
| Advanced Filters | ✅ | Law enforcement filters |
| Contact Information | ✅ | View reporter details |
| Audit Trail Access | ✅ | Case-related logs |
| Generate Reports | ✅ | Official reports |
| Mark Cases as Closed | ✅ | Case resolution |
| User Management | ❌ | Admin only |
| System Settings | ❌ | Admin only |
| Financial Data | ❌ | Admin only |

---

### **🏥 NGO WORKER (Requires Verification)**
**Access Level**: Organization capabilities

| Feature | Access | Description |
|---------|--------|-------------|
| All Citizen Features | ✅ | Inherit all citizen access |
| Report Found Persons | ✅ | Enhanced reporting |
| Organization Dashboard | ✅ | NGO-specific views |
| Batch Reporting | ✅ | Multiple reports |
| Advanced Search | ✅ | Organization filters |
| Contact Information | ✅ | Limited access |
| Generate Reports | ✅ | Organization reports |
| Volunteer Management | ✅ | Manage volunteers |
| Verify Cases | ❌ | Police/Admin only |
| User Management | ❌ | Admin only |
| System Settings | ❌ | Admin only |

---

### **🤝 VOLUNTEER (Requires Verification)**
**Access Level**: Community helper capabilities

| Feature | Access | Description |
|---------|--------|-------------|
| All Citizen Features | ✅ | Inherit all citizen access |
| Enhanced Reporting | ✅ | Priority reporting |
| Volunteer Dashboard | ✅ | Volunteer-specific views |
| Advanced Search | ✅ | Extended filters |
| Contact Information | ⚠️ | Limited access |
| Generate Reports | ✅ | Volunteer reports |
| Verify Cases | ❌ | Police/Admin only |
| User Management | ❌ | Admin only |
| System Settings | ❌ | Admin only |

---

### **🔧 ADMINISTRATOR (System Owner)**
**Access Level**: Full system control

| Feature | Access | Description |
|---------|--------|-------------|
| All User Features | ✅ | Complete system access |
| User Management | ✅ | Create/edit/delete users |
| Role Assignment | ✅ | Change user roles |
| Verification System | ✅ | Approve/reject verifications |
| System Settings | ✅ | Configure platform |
| Audit Logs | ✅ | Full audit trail access |
| Database Management | ✅ | Direct database access |
| Security Settings | ✅ | Configure security |
| Backup & Restore | ✅ | System maintenance |
| API Management | ✅ | Control API access |
| Financial Data | ✅ | All financial information |
| Analytics | ✅ | Complete system analytics |

---

## 🔐 **Security Implementation Details**

### **🛡️ Authentication Security**
- **Rate Limiting**: 5 failed attempts → 30-minute lockout
- **Password Requirements**: 8+ chars, uppercase, lowercase, digit, special char
- **Session Security**: User agent validation, 24-hour session expiry
- **Account Lockout**: Automatic protection against brute force
- **Audit Logging**: All login/logout events recorded

### **🔍 Access Control Implementation**
```python
# Decorators for role-based access
@login_required                    # Must be logged in
@role_required(['police', 'admin'])  # Specific roles only
@verified_required                # Must be verified
@admin_required                   # Admin only
@police_required                  # Police or admin
@ngo_required                     # NGO or admin
@volunteer_required               # Volunteer+ roles
```

### **📊 Data Access by Role**

#### **🔒 Sensitive Data Protection**
- **Personal Contact Info**: Police + Admin only
- **ID Documents**: Admin only (stored securely)
- **Audit Logs**: Admin only
- **System Configuration**: Admin only
- **Financial Data**: Admin only

#### **🌐 Public Information**
- **Case Details**: Basic info only (name, age, location)
- **Photos**: Publicly accessible
- **Search Results**: Filtered for public
- **Statistics**: Aggregated data only

---

## 🔄 **Workflow Processes**

### **1. USER REGISTRATION WORKFLOW**
```
Start → Choose Role → Fill Form → Upload Documents (if required) → 
Email/Phone Validation → Account Created → 
[If Citizen] Auto-Verify → Full Access
[If Police/NGO] Pending Admin Review → Limited Access → Admin Approval → Full Access
```

### **2. MISSING PERSON REPORT WORKFLOW**
```
Citizen Reports → AI Face Matching → 
[If Found] Auto-Match → Admin Review → 
[If Verified] Public Display → 
[If Match Found] Notify Reporter → Case Closed
```

### **3. FOUND PERSON REPORT WORKFLOW**
```
Organization Reports → AI Face Matching → 
[If Match Found] Create Potential Match → 
Police Review → 
[If Confirmed] Notify Missing Person Reporter → Reunification
```

### **4. VERIFICATION WORKFLOW**
```
New User Registration → 
[Police/NGO] Document Upload → 
Admin Review → 
[Approved] Verified Status → Full Role Access
[Rejected] Account Deactivated → Notification
```

---

## 📱 **Mobile App Integration**

### **API Access by Role**
- **Public**: Read-only access to public data
- **Citizen**: Full reporting + search capabilities
- **Police**: Enhanced access + verification powers
- **NGO**: Organization-specific features
- **Admin**: Full API access

### **Security Features**
- **API Key Authentication**: Role-based API keys
- **Rate Limiting**: Per-user API limits
- **Data Encryption**: All sensitive data encrypted
- **Audit Trail**: All API calls logged

---

## 🚨 **Security Incident Response**

### **Account Lockout Procedure**
1. **5 Failed Attempts** → 30-minute lockout
2. **Suspicious Activity** → Admin notification
3. **Brute Force Attack** → IP blocking
4. **Account Recovery** → Email verification

### **Data Breach Protocol**
1. **Immediate Detection** → Audit log analysis
2. **User Notification** → Email alerts
3. **Password Reset** → Forced password changes
4. **System Lockdown** → Temporary access restrictions
5. **Investigation** → Full security audit

---

## 📈 **System Monitoring**

### **Key Metrics Tracked**
- **Login Attempts**: Success/failure rates
- **Account Creation**: New registrations by role
- **Case Reports**: Volume and resolution rates
- **Face Matches**: AI matching accuracy
- **API Usage**: Request volumes and errors

### **Alerts Configured**
- **Failed Login Spikes**: Potential attacks
- **Account Lockouts**: Security incidents
- **System Errors**: Technical issues
- **High-Volume Usage**: Performance monitoring

---

## 🔧 **Configuration Options**

### **Security Settings**
```python
# Password requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True

# Rate limiting
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 1800  # 30 minutes
API_RATE_LIMIT = 100  # requests per minute

# Session security
SESSION_TIMEOUT = 86400  # 24 hours
REQUIRE_SESSION_VALIDATION = True
```

### **Role-Based Features**
```python
# Verification requirements
REQUIRE_VERIFICATION = {
    'citizen': False,
    'police': True,
    'ngo': True,
    'volunteer': True,
    'admin': False  # Created by existing admin
}

# Default permissions
DEFAULT_PERMISSIONS = {
    'citizen': ['report', 'search', 'contact'],
    'police': ['verify', 'investigate', 'admin_panel'],
    'ngo': ['organize', 'report', 'volunteer_manage'],
    'volunteer': ['report', 'search', 'assist'],
    'admin': ['all_permissions']
}
```

---

## 🎯 **Best Practices Implemented**

### **✅ Security Best Practices**
- Multi-layer authentication
- Role-based access control
- Comprehensive audit logging
- Rate limiting and lockout protection
- Secure password policies
- Session security validation
- Data encryption at rest and in transit

### **✅ User Experience Best Practices**
- Clear role definitions
- Progressive disclosure of features
- Intuitive workflow processes
- Mobile-responsive design
- Real-time notifications
- Comprehensive help system

### **✅ System Reliability Best Practices**
- Redundant security measures
- Graceful error handling
- Comprehensive testing
- Performance monitoring
- Regular security audits
- Disaster recovery procedures

---

This comprehensive authentication and authorization system ensures that VanishVault maintains security while providing appropriate access to all user types involved in the missing person identification process.
