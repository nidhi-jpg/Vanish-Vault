#!/usr/bin/env python
"""
Automated test users creation script for VanishVault.
Creates test accounts for all user roles with proper permissions and verification.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import MissingPerson, FoundPerson

User = get_user_model()


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def create_test_users():
    """Create test users for all roles."""
    print_header("Creating Test Users for VanishVault Testing")
    
    test_users = [
        {
            'username': 'admin_test',
            'email': 'admin@vanishvault.test',
            'password': 'AdminTest123!',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': User.Roles.ADMIN,
            'phone_number': '+12345678901',
            'organization': 'VanishVault System Administration',
            'is_verified': True,
            'description': 'System administrator with full access'
        },
        {
            'username': 'police_test',
            'email': 'police@vanishvault.test',
            'password': 'PoliceTest123!',
            'first_name': 'Police',
            'last_name': 'Officer',
            'role': User.Roles.POLICE,
            'phone_number': '+12345678902',
            'organization': 'City Police Department',
            'is_verified': True,
            'description': 'Police officer with case verification powers'
        },
        {
            'username': 'ngo_test',
            'email': 'ngo@vanishvault.test',
            'password': 'NgoTest123!',
            'first_name': 'NGO',
            'last_name': 'Coordinator',
            'role': User.Roles.NGO,
            'phone_number': '+12345678903',
            'organization': 'Helping Hands NGO',
            'is_verified': True,
            'description': 'NGO coordinator for missing person assistance'
        },
        {
            'username': 'citizen_test',
            'email': 'citizen@vanishvault.test',
            'password': 'CitizenTest123!',
            'first_name': 'Citizen',
            'last_name': 'User',
            'role': User.Roles.CITIZEN,
            'phone_number': '+12345678904',
            'organization': '',
            'is_verified': True,
            'description': 'Regular citizen user for testing'
        },
        {
            'username': 'volunteer_test',
            'email': 'volunteer@vanishvault.test',
            'password': 'VolunteerTest123!',
            'first_name': 'Volunteer',
            'last_name': 'Helper',
            'role': User.Roles.VOLUNTEER,
            'phone_number': '+12345678905',
            'organization': 'Community Volunteers',
            'is_verified': True,
            'description': 'Volunteer user for community assistance'
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            # Check if user already exists
            if User.objects.filter(username=user_data['username']).exists():
                user = User.objects.get(username=user_data['username'])
                print(f"✓ User '{user.username}' already exists")
                created_users.append(user)
                continue
            
            # Create new user
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                phone_number=user_data['phone_number'],
                organization=user_data['organization'],
                is_verified=user_data['is_verified']
            )
            
            print(f"✓ Created {user_data['role']} user: {user.username}")
            print(f"  - Email: {user.email}")
            print(f"  - Role: {user.get_role_display()}")
            print(f"  - Verified: {user.is_verified}")
            print(f"  - Organization: {user.organization}")
            print(f"  - Description: {user_data['description']}")
            
            created_users.append(user)
            
        except Exception as e:
            print(f"✗ Failed to create user '{user_data['username']}': {e}")
    
    return created_users


def create_test_cases():
    """Create test missing and found person cases."""
    print_header("Creating Test Cases for System Testing")
    
    # Get test users
    try:
        citizen = User.objects.get(username='citizen_test')
        police = User.objects.get(username='police_test')
        ngo = User.objects.get(username='ngo_test')
    except User.DoesNotExist as e:
        print(f"✗ Test users not found: {e}")
        return
    
    # Create test missing person cases
    missing_cases = [
        {
            'full_name': 'John Smith',
            'age': 25,
            'gender': 'male',
            'height': '5\'10"',
            'weight': '160 lbs',
            'hair_color': 'Brown',
            'eye_color': 'Blue',
            'distinguishing_features': 'Tattoo on right arm',
            'last_seen_location': 'Central Park, New York',
            'last_seen_date': '2024-01-15',
            'last_seen_time': '14:30:00',
            'description': 'Missing after jogging in Central Park',
            'reporter_relationship': 'Friend',
            'reporter_phone': '+12345678900',
            'status': 'verified'
        },
        {
            'full_name': 'Emily Johnson',
            'age': 32,
            'gender': 'female',
            'height': '5\'6"',
            'weight': '130 lbs',
            'hair_color': 'Blonde',
            'eye_color': 'Green',
            'distinguishing_features': 'Small scar on forehead',
            'last_seen_location': 'Shopping Mall, Los Angeles',
            'last_seen_date': '2024-01-20',
            'last_seen_time': '19:00:00',
            'description': 'Last seen leaving shopping mall',
            'reporter_relationship': 'Sister',
            'reporter_phone': '+12345678901',
            'status': 'pending'
        }
    ]
    
    for case_data in missing_cases:
        try:
            # Check if case already exists
            if MissingPerson.objects.filter(full_name=case_data['full_name']).exists():
                print(f"✓ Missing person case '{case_data['full_name']}' already exists")
                continue
            
            case = MissingPerson.objects.create(
                reporter=citizen,
                **case_data
            )
            print(f"✓ Created missing person case: {case.full_name} (ID: {case.case_id})")
            
        except Exception as e:
            print(f"✗ Failed to create missing case '{case_data['full_name']}': {e}")
    
    # Create test found person cases
    found_cases = [
        {
            'possible_name': 'Unknown Male',
            'estimated_age': 25,
            'gender': 'male',
            'height': '5\'10"',
            'weight': '160 lbs',
            'hair_color': 'Brown',
            'eye_color': 'Blue',
            'distinguishing_features': 'Tattoo on right arm',
            'found_location': 'Hospital Emergency Room',
            'found_date': '2024-01-16',
            'found_time': '22:00:00',
            'notes': 'Found unconscious, no identification',
            'found_by_organization': 'City General Hospital',
            'contact_person': 'Dr. Sarah Wilson',
            'contact_phone': '+12345678902',
            'status': 'unidentified'
        },
        {
            'possible_name': 'Jane Doe',
            'estimated_age': 30,
            'gender': 'female',
            'height': '5\'6"',
            'weight': '130 lbs',
            'hair_color': 'Blonde',
            'eye_color': 'Green',
            'distinguishing_features': 'Small scar on forehead',
            'found_location': 'Bus Station',
            'found_date': '2024-01-21',
            'found_time': '06:00:00',
            'notes': 'Found sleeping at bus station',
            'found_by_organization': 'Helping Hands NGO',
            'contact_person': 'Volunteer Coordinator',
            'contact_phone': '+12345678903',
            'status': 'unidentified'
        }
    ]
    
    for case_data in found_cases:
        try:
            # Check if case already exists
            if FoundPerson.objects.filter(possible_name=case_data['possible_name']).exists():
                print(f"✓ Found person case '{case_data['possible_name']}' already exists")
                continue
            
            case = FoundPerson.objects.create(**case_data)
            print(f"✓ Created found person case: {case.possible_name} (ID: {case.case_id})")
            
        except Exception as e:
            print(f"✗ Failed to create found case '{case_data['possible_name']}': {e}")


def create_sample_photos():
    """Create sample photo files for testing."""
    print_header("Creating Sample Photos for Testing")
    
    try:
        from PIL import Image
        import io
        
        # Create a simple test image
        def create_test_image(filename, color='blue'):
            image = Image.new('RGB', (300, 400), color=color)
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG')
            img_buffer.seek(0)
            return SimpleUploadedFile(
                filename,
                img_buffer.getvalue(),
                content_type='image/jpeg'
            )
        
        # Create test photos for missing persons
        missing_persons = MissingPerson.objects.all()[:2]
        for i, person in enumerate(missing_persons):
            if not person.photo:
                photo = create_test_image(f'missing_{i+1}.jpg', 'lightblue')
                person.photo.save(f'missing_{person.case_id}.jpg', photo, save=True)
                print(f"✓ Added photo to missing person: {person.full_name}")
        
        # Create test photos for found persons
        found_persons = FoundPerson.objects.all()[:2]
        for i, person in enumerate(found_persons):
            if not person.photo:
                photo = create_test_image(f'found_{i+1}.jpg', 'lightgreen')
                person.photo.save(f'found_{person.case_id}.jpg', photo, save=True)
                print(f"✓ Added photo to found person: {person.possible_name}")
        
    except ImportError:
        print("⚠️  PIL not available. Skipping photo creation.")
    except Exception as e:
        print(f"✗ Failed to create sample photos: {e}")


def display_test_summary():
    """Display summary of created test data."""
    print_header("Test Data Summary")
    
    print("📊 Test Users Created:")
    for user in User.objects.filter(username__contains='_test'):
        status = "✅ Verified" if user.is_verified else "⏳ Pending"
        print(f"  {user.username} ({user.get_role_display()}) - {status}")
    
    print(f"\n📋 Missing Person Cases: {MissingPerson.objects.count()}")
    for case in MissingPerson.objects.all():
        print(f"  {case.full_name} - {case.case_id} - {case.status}")
    
    print(f"\n🔍 Found Person Cases: {FoundPerson.objects.count()}")
    for case in FoundPerson.objects.all():
        print(f"  {case.possible_name} - {case.case_id} - {case.status}")
    
    print(f"\n📸 Photos in System:")
    missing_with_photos = MissingPerson.objects.exclude(photo='').count()
    found_with_photos = FoundPerson.objects.exclude(photo='').count()
    print(f"  Missing persons with photos: {missing_with_photos}")
    print(f"  Found persons with photos: {found_with_photos}")


def main():
    """Main function to create all test data."""
    print_header("VanishVault Test Data Creation Script")
    print("This script creates test users and cases for system testing.")
    
    try:
        # Create test users
        users = create_test_users()
        
        # Create test cases
        create_test_cases()
        
        # Create sample photos
        create_sample_photos()
        
        # Display summary
        display_test_summary()
        
        print_header("✅ Test Data Creation Complete")
        print("🎯 You can now test the system using these credentials:")
        print("\n📋 Login Credentials:")
        print("  Admin: admin_test / AdminTest123!")
        print("  Police: police_test / PoliceTest123!")
        print("  NGO: ngo_test / NgoTest123!")
        print("  Citizen: citizen_test / CitizenTest123!")
        print("  Volunteer: volunteer_test / VolunteerTest123!")
        
        print("\n🌐 Next Steps:")
        print("1. Start the server: python manage.py runserver")
        print("2. Open browser: http://localhost:8000")
        print("3. Follow the COMPREHENSIVE_TESTING_GUIDE.md")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
