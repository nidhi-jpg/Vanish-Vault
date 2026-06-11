#!/usr/bin/env python
import os
import django
from datetime import date, timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from core.models import User, MissingPerson, FoundPerson, Sighting

def create_sample_data():
    print("Creating sample data for VanishVault...")
    
    # Create sample missing persons
    sample_missing = [
        {
            'full_name': 'Sarah Johnson',
            'age': 28,
            'gender': 'female',
            'height': '5\'6"',
            'weight': '130 lbs',
            'hair_color': 'Brown',
            'eye_color': 'Blue',
            'distinguishing_features': 'Small scar on left cheek, tattoo of butterfly on right wrist',
            'last_seen_location': 'Central Park, New York',
            'last_seen_date': date.today() - timedelta(days=5),
            'last_seen_time': '14:30',
            'description': 'Sarah was last seen walking in Central Park. She was wearing a blue jacket and jeans.',
            'status': 'verified',
            'reporter_relationship': 'Sister',
            'reporter_phone': '+1-555-0123'
        },
        {
            'full_name': 'Michael Chen',
            'age': 45,
            'gender': 'male',
            'height': '5\'10"',
            'weight': '180 lbs',
            'hair_color': 'Black',
            'eye_color': 'Brown',
            'distinguishing_features': 'Glasses, mole on right temple',
            'last_seen_location': 'Downtown Seattle, WA',
            'last_seen_date': date.today() - timedelta(days=12),
            'last_seen_time': '09:15',
            'description': 'Michael was last seen leaving his office building. He was wearing a gray suit.',
            'status': 'verified',
            'reporter_relationship': 'Wife',
            'reporter_phone': '+1-555-0456'
        },
        {
            'full_name': 'Emma Rodriguez',
            'age': 16,
            'gender': 'female',
            'height': '5\'4"',
            'weight': '120 lbs',
            'hair_color': 'Blonde',
            'eye_color': 'Green',
            'distinguishing_features': 'Braces, pierced ears',
            'last_seen_location': 'High School, Los Angeles, CA',
            'last_seen_date': date.today() - timedelta(days=8),
            'last_seen_time': '15:45',
            'description': 'Emma was last seen leaving school. She was wearing a pink backpack.',
            'status': 'pending',
            'reporter_relationship': 'Mother',
            'reporter_phone': '+1-555-0789'
        },
        {
            'full_name': 'David Thompson',
            'age': 62,
            'gender': 'male',
            'height': '6\'0"',
            'weight': '200 lbs',
            'hair_color': 'Gray',
            'eye_color': 'Blue',
            'distinguishing_features': 'Walking cane, hearing aid',
            'last_seen_location': 'Grocery Store, Chicago, IL',
            'last_seen_date': date.today() - timedelta(days=3),
            'last_seen_time': '11:20',
            'description': 'David was last seen shopping for groceries. He was wearing a brown coat.',
            'status': 'verified',
            'reporter_relationship': 'Son',
            'reporter_phone': '+1-555-0321'
        },
        {
            'full_name': 'Lisa Park',
            'age': 34,
            'gender': 'female',
            'height': '5\'7"',
            'weight': '140 lbs',
            'hair_color': 'Black',
            'eye_color': 'Brown',
            'distinguishing_features': 'Tattoo of rose on left shoulder',
            'last_seen_location': 'Restaurant District, Miami, FL',
            'last_seen_date': date.today() - timedelta(days=15),
            'last_seen_time': '19:30',
            'description': 'Lisa was last seen having dinner with friends. She was wearing a red dress.',
            'status': 'verified',
            'reporter_relationship': 'Friend',
            'reporter_phone': '+1-555-0654'
        }
    ]
    
    # Create missing person records
    for data in sample_missing:
        person, created = MissingPerson.objects.get_or_create(
            full_name=data['full_name'],
            defaults=data
        )
        if created:
            print(f"Created missing person: {person.full_name}")
    
    # Create sample found persons
    sample_found = [
        {
            'possible_name': 'Unknown Male',
            'estimated_age': 45,
            'gender': 'male',
            'height': '5\'9"',
            'weight': '175 lbs',
            'hair_color': 'Brown',
            'eye_color': 'Blue',
            'distinguishing_features': 'Beard, scar on right hand',
            'found_location': 'Hospital Emergency Room, Phoenix, AZ',
            'found_date': date.today() - timedelta(days=2),
            'found_time': '08:30',
            'notes': 'Found unconscious near highway. No identification found.',
            'status': 'unidentified',
            'found_by_organization': 'Phoenix General Hospital',
            'contact_person': 'Dr. Smith',
            'contact_phone': '+1-555-0987'
        },
        {
            'possible_name': 'Unknown Female',
            'estimated_age': 25,
            'gender': 'female',
            'height': '5\'5"',
            'weight': '125 lbs',
            'hair_color': 'Blonde',
            'eye_color': 'Green',
            'distinguishing_features': 'Tattoo of star on ankle',
            'found_location': 'Shelter, Denver, CO',
            'found_date': date.today() - timedelta(days=7),
            'found_time': '14:00',
            'notes': 'Found at homeless shelter. Appears confused and disoriented.',
            'status': 'unidentified',
            'found_by_organization': 'Denver Homeless Shelter',
            'contact_person': 'Jane Doe',
            'contact_phone': '+1-555-0543'
        }
    ]
    
    # Create found person records
    for data in sample_found:
        person, created = FoundPerson.objects.get_or_create(
            possible_name=data['possible_name'],
            found_location=data['found_location'],
            defaults=data
        )
        if created:
            print(f"Created found person: {person.possible_name}")
    
    # Create sample sightings
    missing_persons = MissingPerson.objects.filter(status='verified')[:3]
    sighting_locations = [
        'Bus Station, Downtown',
        'Shopping Mall, North Side',
        'Park, Central District',
        'Gas Station, Highway 101',
        'Library, University Area'
    ]
    
    for person in missing_persons:
        # Create 1-2 sightings per person
        num_sightings = random.randint(1, 2)
        for i in range(num_sightings):
            sighting_date = date.today() - timedelta(days=random.randint(1, 10))
            sighting = Sighting.objects.create(
                missing_person=person,
                location=random.choice(sighting_locations),
                date=sighting_date,
                time=f"{random.randint(8, 20):02d}:{random.randint(0, 59):02d}",
                description=f"I saw someone who looked like {person.full_name} at {random.choice(sighting_locations)}. They seemed to be in good condition.",
                confidence_level=random.choice(['high', 'medium', 'low']),
                reporter_name=f"Anonymous Reporter {i+1}",
                reporter_phone=f"+1-555-{random.randint(1000, 9999)}",
                status='new'
            )
            print(f"Created sighting for {person.full_name}")
    
    print("\n✅ Sample data created successfully!")
    print(f"Missing Persons: {MissingPerson.objects.count()}")
    print(f"Found Persons: {FoundPerson.objects.count()}")
    print(f"Sightings: {Sighting.objects.count()}")

if __name__ == "__main__":
    create_sample_data()
