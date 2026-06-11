#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from core.models import User, MissingPerson, FoundPerson, Sighting, VerificationTask, Notification, AuditLog, Photo

def show_database():
    print("=" * 60)
    print("VANISHVAULT DATABASE CONTENTS")
    print("=" * 60)
    
    # Users
    print(f"\n👥 USERS ({User.objects.count()} total)")
    print("-" * 40)
    for user in User.objects.all():
        print(f"ID: {user.id} | Username: {user.username} | Role: {user.get_role_display()} | Verified: {user.is_verified}")
        print(f"    Name: {user.get_full_name() or 'N/A'} | Email: {user.email}")
        print(f"    Organization: {user.organization or 'N/A'}")
        print()
    
    # Missing Persons
    print(f"\n🔍 MISSING PERSONS ({MissingPerson.objects.count()} total)")
    print("-" * 40)
    for person in MissingPerson.objects.all():
        print(f"ID: {person.id} | Case ID: {person.case_id} | Name: {person.full_name}")
        print(f"    Age: {person.age or 'N/A'} | Gender: {person.get_gender_display()}")
        print(f"    Status: {person.get_status_display()} | Last Seen: {person.last_seen_location}")
        print(f"    Created: {person.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Reporter: {person.reporter.username if person.reporter else 'Anonymous'}")
        print()
    
    # Found Persons
    print(f"\n🏥 FOUND PERSONS ({FoundPerson.objects.count()} total)")
    print("-" * 40)
    for person in FoundPerson.objects.all():
        print(f"ID: {person.id} | Case ID: {person.case_id} | Name: {person.possible_name or 'Unidentified'}")
        print(f"    Age: {person.estimated_age or 'N/A'} | Gender: {person.get_gender_display()}")
        print(f"    Status: {person.get_status_display()} | Found: {person.found_location}")
        print(f"    Created: {person.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Organization: {person.found_by_organization}")
        print()
    
    # Sightings
    print(f"\n👁️ SIGHTINGS ({Sighting.objects.count()} total)")
    print("-" * 40)
    for sighting in Sighting.objects.all():
        print(f"ID: {sighting.id} | Person: {sighting.missing_person.full_name}")
        print(f"    Location: {sighting.location} | Date: {sighting.date}")
        print(f"    Status: {sighting.get_status_display()} | Confidence: {sighting.get_confidence_level_display()}")
        print(f"    Reporter: {sighting.reporter_name or 'Anonymous'}")
        print()
    
    # Verification Tasks
    print(f"\n✅ VERIFICATION TASKS ({VerificationTask.objects.count()} total)")
    print("-" * 40)
    for task in VerificationTask.objects.all():
        print(f"ID: {task.id} | Type: {task.get_task_type_display()}")
        print(f"    Status: {task.get_status_display()} | Priority: {task.get_priority_display()}")
        print(f"    Assigned to: {task.assigned_to.username if task.assigned_to else 'Unassigned'}")
        print(f"    Description: {task.description[:50]}...")
        print()
    
    # Notifications
    print(f"\n🔔 NOTIFICATIONS ({Notification.objects.count()} total)")
    print("-" * 40)
    for notification in Notification.objects.all():
        print(f"ID: {notification.id} | User: {notification.user.username}")
        print(f"    Type: {notification.get_notification_type_display()}")
        print(f"    Title: {notification.title}")
        print(f"    Read: {notification.is_read} | Created: {notification.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    # Audit Logs
    print(f"\n📋 AUDIT LOGS ({AuditLog.objects.count()} total)")
    print("-" * 40)
    for log in AuditLog.objects.all()[:10]:  # Show only last 10
        print(f"ID: {log.id} | User: {log.user.username if log.user else 'System'}")
        print(f"    Action: {log.get_action_display()} | Model: {log.model_name}")
        print(f"    Object ID: {log.object_id} | Created: {log.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    # Photos
    print(f"\n📸 PHOTOS ({Photo.objects.count()} total)")
    print("-" * 40)
    for photo in Photo.objects.all():
        print(f"ID: {photo.id} | Caption: {photo.caption or 'No caption'}")
        print(f"    Uploaded by: {photo.uploaded_by.username if photo.uploaded_by else 'Anonymous'}")
        print(f"    Uploaded: {photo.uploaded_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Image: {photo.image}")
        print()
    
    print("=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)
    print(f"Total Users: {User.objects.count()}")
    print(f"Total Missing Persons: {MissingPerson.objects.count()}")
    print(f"Total Found Persons: {FoundPerson.objects.count()}")
    print(f"Total Sightings: {Sighting.objects.count()}")
    print(f"Total Verification Tasks: {VerificationTask.objects.count()}")
    print(f"Total Notifications: {Notification.objects.count()}")
    print(f"Total Audit Logs: {AuditLog.objects.count()}")
    print(f"Total Photos: {Photo.objects.count()}")

if __name__ == "__main__":
    show_database()
