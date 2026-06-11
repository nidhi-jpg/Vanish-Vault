# VanishVault Notification System Setup Guide

## Overview
This comprehensive notification system handles all user communications with role-based delivery, email notifications, and a centralized activity feed.

## Database Schema

### Core Models

#### 1. Notification
- **recipient**: User who receives the notification
- **sender**: User who triggered the notification (optional)
- **notification_type**: Type (case_submitted, case_verified, etc.)
- **priority**: Priority level (low, medium, high, urgent)
- **title**: Notification title
- **message**: Detailed message
- **missing_person**: Related case (optional)
- **sighting**: Related sighting (optional)
- **data**: JSON field for additional data
- **is_read**: Read status
- **is_email_sent**: Email delivery status
- **created_at**: Timestamp
- **read_at**: When marked as read
- **expires_at**: Optional expiration

#### 2. NotificationTemplate
- Email templates for different notification types
- Subject and body templates using Django template syntax

#### 3. NotificationPreference
- User-specific notification preferences
- Separate email and in-app preferences per notification type

#### 4. FaceSearchLog
- Audit log for all face search operations
- Stores match scores, uploaded images, performer details
- IP address and user agent tracking

## Installation Steps

### 1. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Update Models Import
Add to `core/models.py`:
```python
from .notification_models import (
    Notification, NotificationTemplate, 
    NotificationPreference, FaceSearchLog
)
```

### 3. Update URLs
Add to `core/urls.py`:
```python
path('notifications/', views.notification_center, name='notification_center'),
path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
```

### 4. Integration Points

#### A. Case Registration (create_missing_person view)
```python
from .services.notification_service import NotificationService

# After creating missing_person:
NotificationService.notify_case_submitted(missing_person)
```

#### B. Case Verification (verify_missing_person view)
```python
if action == 'verify':
    # ... verification logic ...
    NotificationService.notify_case_verified(missing_person, request.user)
elif action == 'reject':
    # ... rejection logic ...
    NotificationService.notify_case_rejected(missing_person, request.user, rejection_reason)
```

#### C. Sighting Reports (report_sighting view)
```python
# After creating sighting:
NotificationService.notify_sighting_reported(sighting)
```

#### D. Face Search (face_search view)
```python
# After face search logic:
search_log = NotificationService.log_face_search(
    performed_by=request.user,
    missing_person=missing_person,
    uploaded_image=uploaded_file,
    match_score=match_score,
    matched_person=matched_person,
    search_results=search_results,
    ip_address=get_client_ip(request),
    user_agent=request.META.get('HTTP_USER_AGENT', '')
)
```

#### E. Police Assignment
```python
NotificationService.notify_police_assigned(missing_person, officer, request.user)
```

#### F. Status Updates
```python
NotificationService.notify_case_status_updated(
    missing_person, old_status, new_status, request.user
)
```

### 5. Admin Dashboard Integration

Update `dashboard` view in `core/views.py`:
```python
def dashboard(request):
    # ... existing logic ...
    
    # Add notification data
    from .services.notification_service import NotificationService
    from .notification_models import Notification, FaceSearchLog
    
    # Recent activity
    recent_notifications = Notification.objects.select_related(
        'sender', 'recipient', 'missing_person', 'sighting'
    ).order_by('-created_at')[:20]
    
    # Recent face searches
    recent_face_searches = FaceSearchLog.objects.select_related(
        'performed_by', 'missing_person', 'matched_person'
    ).order_by('-created_at')[:10]
    
    # High confidence matches
    high_confidence_matches = FaceSearchLog.objects.filter(
        match_score__gte=0.85
    ).select_related('performed_by', 'missing_person').order_by('-created_at')[:5]
    
    context.update({
        'recent_notifications': recent_notifications,
        'recent_face_searches': recent_face_searches,
        'high_confidence_matches': high_confidence_matches,
    })
    
    return render(request, 'core/dashboard.html', context)
```

### 6. Template Updates

#### Add to base.html (notification bell):
```html
<li class="nav-item dropdown">
    <a class="nav-link position-relative" href="#" id="notificationDropdown" role="button" data-bs-toggle="dropdown">
        <i class="bi bi-bell"></i>
        {% if request.user.notifications.filter(is_read=False).count > 0 %}
        <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
            {{ request.user.notifications.filter(is_read=False).count }}
        </span>
        {% endif %}
    </a>
    <ul class="dropdown-menu dropdown-menu-end" style="width: 300px;">
        {% for notification in request.user.notifications.all|slice:":5" %}
        <li class="dropdown-item">
            <small class="{{ 'fw-bold' if not notification.is_read }}">
                {{ notification.title }}
            </small>
            <br>
            <small class="text-muted">{{ notification.created_at|timesince }} ago</small>
        </li>
        {% empty %}
        <li><span class="dropdown-item text-muted">No notifications</span></li>
        {% endfor %}
        <li><hr class="dropdown-divider"></li>
        <li><a class="dropdown-item" href="{% url 'core:notification_center' %}">View All</a></li>
    </ul>
</li>
```

#### Add to dashboard.html (activity feed):
```html
{% include 'core/admin_activity_feed.html' %}
```

### 7. Email Configuration

Update `settings.py`:
```python
# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'VanishVault <noreply@vanishvault.com>'
SITE_URL = 'http://localhost:8000'
```

### 8. Create Notification Templates

Create email templates in `templates/emails/`:
- `case_submitted.html`
- `case_verified.html`
- `case_rejected.html`
- `sighting_reported.html`
- `high_confidence_match.html`

### 9. Automated Cleanup

Create management command for cleanup:
```python
# core/management/commands/cleanup_notifications.py
from django.core.management.base import BaseCommand
from core.services.notification_service import NotificationService

class Command(BaseCommand):
    def handle(self, *args, **options):
        deleted_count = NotificationService.cleanup_old_notifications(days_old=30)
        self.stdout.write(f'Cleaned up {deleted_count} old notifications')
```

Schedule with cron:
```bash
0 2 * * * /path/to/venv/bin/python /path/to/manage.py cleanup_notifications
```

## Notification Types and Triggers

### 1. Case Registration
- **Trigger**: New missing person case submitted
- **Recipients**: Police (high), Admin (medium), Citizen (medium)
- **Message**: "New case pending verification"

### 2. Case Verification
- **Trigger**: Police verifies/rejects case
- **Recipients**: Citizen (high), Admin (medium)
- **Message**: "Your case has been verified" or rejection reason

### 3. Case Status Updates
- **Trigger**: Status changes (investigation, found, closed)
- **Recipients**: Citizen (medium), Admin (low), Assigned Police (medium)

### 4. Sighting Reports
- **Trigger**: New sighting submitted
- **Recipients**: Assigned Police (high), Admin (medium), Citizen (high)

### 5. Face Search Operations
- **Trigger**: Face search performed
- **Thresholds**:
  - ≥85%: Urgent alert to Police + Admin + Citizen
  - ≥70%: High priority to Police + Admin
  - <70%: Log only

## Performance Optimizations

### 1. Database Indexes
All models include proper indexes for:
- Recipient + read status
- Notification type
- Priority
- Creation date
- Match scores (FaceSearchLog)

### 2. Query Optimization
- Use `select_related` for foreign keys
- Limit results in activity feeds
- Batch email sending

### 3. Caching
- Cache notification counts
- Cache user preferences
- Cache email templates

## Security Considerations

### 1. Access Control
- Users can only see their own notifications
- Admin can see all notifications
- IP tracking for face searches

### 2. Data Privacy
- Sensitive data in JSON field
- Email preferences respected
- Audit trail for all actions

### 3. Rate Limiting
- Limit face search attempts
- Limit notification creation
- Prevent email spam

## Monitoring and Analytics

### 1. Key Metrics
- Notification delivery rate
- Email open rates
- Face search success rates
- High confidence match frequency

### 2. Admin Dashboard
- Global activity feed
- Real-time face search alerts
- Notification statistics
- User engagement metrics

## Testing

### 1. Unit Tests
```python
# tests/test_notifications.py
def test_case_submission_notifications():
    # Test notification creation for case submission
    pass

def test_face_search_logging():
    # Test face search logging and notifications
    pass
```

### 2. Integration Tests
- End-to-end notification flow
- Email delivery testing
- Performance testing

## Troubleshooting

### Common Issues

1. **Emails not sending**
   - Check SMTP settings
   - Verify email configuration
   - Check email queue

2. **Notifications not appearing**
   - Check user preferences
   - Verify database migrations
   - Check notification creation

3. **Performance issues**
   - Check database indexes
   - Monitor query performance
   - Consider caching

### Debug Tools
- Django admin for notification management
- Logging for email delivery
- Activity feed for real-time monitoring

## Future Enhancements

1. **Real-time Updates**: WebSocket integration for live notifications
2. **Push Notifications**: Mobile app push notifications
3. **SMS Integration**: SMS notifications for urgent alerts
4. **Analytics Dashboard**: Advanced analytics and reporting
5. **Automation Rules**: Custom notification rules and workflows
