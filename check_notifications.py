import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from core.models import Notification, User

print('=== NOTIFICATION SYSTEM STATUS ===')

# Check total notifications
total_notifications = Notification.objects.count()
print(f'Total notifications: {total_notifications}')

# Check recent notifications
recent = Notification.objects.order_by('-created_at')[:5]
print(f'\nRecent notifications:')
for notif in recent:
    print(f'  - {notif.title} for {notif.recipient.username} ({notif.created_at.strftime("%H:%M")})')

# Check users with notifications
users_with_notifications = Notification.objects.values('recipient__username').distinct().count()
print(f'\nUsers with notifications: {users_with_notifications}')

print('\n=== STATUS COMPLETE ===')
