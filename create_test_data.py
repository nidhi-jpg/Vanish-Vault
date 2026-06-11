#!/usr/bin/env python
"""Create test data for dashboard testing"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import MissingPerson, FoundPerson, PotentialMatch
from django.utils import timezone
import random

User = get_user_model()

def create_test_data():
    print("Creating test data for dashboard...")
    
    # Create test users
    roles = [User.Roles.CITIZEN, User.Roles.POLICE, User.Roles.NGO]
    for i, role in enumerate(roles):
        username = f'test_{role.lower()}_{i}'
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=f'{username}@test.com',
                password='test123',
                role=role,
                is_verified=(role == User.Roles.CITIZEN),  # Only citizens are auto-verified
                first_name=f'Test',
                last_name=f'{role.title()} User'
            )
            print(f'Created user: {username}/test123 (verified: {user.is_verified})')
    
    # Get a citizen user for reporting
    citizen = User.objects.filter(role=User.Roles.CITIZEN).first()
    if not citizen:
        citizen = User.objects.create_user(
            username='test_citizen',
            email='citizen@test.com',
            password='test123',
            role=User.Roles.CITIZEN,
            is_verified=True,
            first_name='Test',
            last_name='Citizen'
        )
    
    # Create test missing persons
    if MissingPerson.objects.count() < 5:
        for i in range(5):
            case = MissingPerson.objects.create(
                full_name=f'Test Missing Person {i+1}',
                age=random.randint(10, 80),
                gender=random.choice(['M', 'F']),
                last_seen_location=f'Test Location {i+1}',
                last_seen_date=timezone.now() - timezone.timedelta(days=random.randint(1, 30)),
                description=f'Test description for missing person {i+1}',
                reporter=citizen,
                status='pending' if i < 3 else 'verified'
            )
            print(f'Created missing case: {case.case_id} (status: {case.status})')
    
    # Create test found persons
    if FoundPerson.objects.count() < 3:
        for i in range(3):
            case = FoundPerson.objects.create(
                possible_name=f'John Doe {i+1}',
                estimated_age=random.randint(10, 80),
                gender=random.choice(['male', 'female']),
                found_location=f'Found Location {i+1}',
                found_date=timezone.now() - timezone.timedelta(days=random.randint(1, 15)),
                found_by_organization=f'Test Organization {i+1}',
                status='unidentified'
            )
            print(f'Created found case: {case.case_id}')
    
    print("\nTest data created successfully!")
    print("\nLogin credentials:")
    print("Admin: admin/admin123")
    print("Test Citizen: test_citizen/test123")
    print("Test Police: test_police_0/test123")
    print("Test NGO: test_ngo_1/test123")

if __name__ == "__main__":
    create_test_data()
