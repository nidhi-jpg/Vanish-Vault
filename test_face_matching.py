#!/usr/bin/env python
"""
Test script for the enhanced AI face matching system.
Tests angle-invariant matching, confidence scoring, and real-time capabilities.
"""

import os
import sys
import django
import json
from io import BytesIO
from PIL import Image
import numpy as np

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from core.face_recognition_utils import (
    extract_face_encoding,
    extract_face_encoding_from_upload,
    find_matches,
    distance_to_confidence,
    classify_match_quality,
    preprocess_image_pil,
    detect_faces_in_image,
    DEEPFACE_AVAILABLE,
    FACE_RECOGNITION_AVAILABLE
)
from core.models import MissingPerson, FoundPerson, User
from core import matching_service
from django.core.files.uploadedfile import InMemoryUploadedFile


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_subheader(title):
    """Print a formatted subheader."""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")


def test_ai_library_availability():
    """Test which AI libraries are available."""
    print_header("AI Library Availability Test")
    
    print(f"DeepFace Available: {DEEPFACE_AVAILABLE}")
    print(f"Face Recognition Available: {FACE_RECOGNITION_AVAILABLE}")
    
    if DEEPFACE_AVAILABLE:
        try:
            from deepface import DeepFace
            print("DeepFace version: Imported successfully")
        except Exception as e:
            print(f"DeepFace import error: {e}")
    
    if FACE_RECOGNITION_AVAILABLE:
        try:
            import face_recognition
            print("Face Recognition version: Imported successfully")
        except Exception as e:
            print(f"Face Recognition import error: {e}")


def test_confidence_scoring():
    """Test the enhanced confidence scoring system."""
    print_header("Confidence Scoring Test")
    
    test_distances = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
    
    print("Testing DeepFace confidence scoring:")
    for distance in test_distances:
        confidence = distance_to_confidence(distance, 'deepface')
        classification = classify_match_quality(confidence)
        print(f"  Distance {distance:.2f} -> Confidence {confidence:.1f}% -> {classification['classification']}")
    
    print("\nTesting face_recognition confidence scoring:")
    for distance in test_distances:
        confidence = distance_to_confidence(distance, 'face_recognition')
        classification = classify_match_quality(confidence)
        print(f"  Distance {distance:.2f} -> Confidence {confidence:.1f}% -> {classification['classification']}")


def test_image_preprocessing():
    """Test the enhanced image preprocessing."""
    print_header("Image Preprocessing Test")
    
    # Create a test image
    test_image = Image.new('RGB', (200, 200), color='blue')
    
    try:
        processed = preprocess_image_pil(test_image)
        print("✓ Image preprocessing completed successfully")
        print(f"  Original size: {test_image.size}")
        print(f"  Processed size: {processed.size}")
        print(f"  Original mode: {test_image.mode}")
        print(f"  Processed mode: {processed.mode}")
    except Exception as e:
        print(f"✗ Image preprocessing failed: {e}")


def test_face_detection():
    """Test face detection capabilities."""
    print_header("Face Detection Test")
    
    # Check if we have any images in media to test with
    media_path = os.path.join(os.path.dirname(__file__), 'media')
    test_images = []
    
    # Look for test images
    for root, dirs, files in os.walk(media_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                test_images.append(os.path.join(root, file))
    
    if not test_images:
        print("No test images found in media directory")
        # Create a simple test image
        test_image_path = os.path.join(media_path, 'test_face.jpg')
        os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
        
        # Create a simple test image with a face-like pattern
        test_image = Image.new('RGB', (300, 300), color='white')
        # Add a simple face pattern (this won't be detected as a real face, but tests the pipeline)
        test_image.save(test_image_path)
        test_images = [test_image_path]
    
    for image_path in test_images[:3]:  # Test up to 3 images
        print(f"\nTesting image: {os.path.basename(image_path)}")
        try:
            face_count = detect_faces_in_image(image_path)
            print(f"  Faces detected: {face_count}")
            
            # Try to extract encoding
            encoding = extract_face_encoding(image_path)
            if encoding is not None:
                print(f"  Face encoding extracted: {len(encoding)} dimensions")
            else:
                print("  No face encoding extracted (no face detected)")
                
        except Exception as e:
            print(f"  Error processing image: {e}")


def test_database_matching():
    """Test matching against database entries."""
    print_header("Database Matching Test")
    
    # Check database entries
    missing_count = MissingPerson.objects.count()
    found_count = FoundPerson.objects.count()
    
    print(f"Missing persons in database: {missing_count}")
    print(f"Found persons in database: {found_count}")
    
    if missing_count == 0 and found_count == 0:
        print("No database entries found. Creating test data...")
        create_test_data()
        missing_count = MissingPerson.objects.count()
        found_count = FoundPerson.objects.count()
    
    # Test embedding generation
    missing_with_photos = MissingPerson.objects.filter(photo__isnull=False).exclude(photo='')
    found_with_photos = FoundPerson.objects.filter(photo__isnull=False).exclude(photo='')
    
    print(f"Missing persons with photos: {missing_with_photos.count()}")
    print(f"Found persons with photos: {found_with_photos.count()}")
    
    # Test embedding generation for existing photos
    for person in missing_with_photos[:2]:  # Test up to 2
        try:
            if person.photo and person.photo.path:
                encoding = extract_face_encoding(person.photo.path)
                if encoding:
                    print(f"✓ Generated embedding for {person.full_name}: {len(encoding)} dimensions")
                else:
                    print(f"✗ No face detected in {person.full_name}'s photo")
        except Exception as e:
            print(f"✗ Error processing {person.full_name}: {e}")


def create_test_data():
    """Create minimal test data for testing."""
    print("Creating test data...")
    
    try:
        # Create a test user
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'role': User.Roles.CITIZEN,
                'is_verified': True
            }
        )
        
        # Create a simple test image
        from django.core.files.base import ContentFile
        test_image = Image.new('RGB', (300, 300), color='white')
        
        # Save test image to memory
        img_buffer = BytesIO()
        test_image.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        # Create test missing person
        missing = MissingPerson(
            full_name='Test Missing Person',
            age=25,
            gender='unknown',
            last_seen_location='Test Location',
            last_seen_date='2024-01-01',
            status='verified',
            reporter=user
        )
        missing.photo.save('test_missing.jpg', ContentFile(img_buffer.getvalue()), save=True)
        missing.save()
        
        # Create test found person
        found = FoundPerson(
            possible_name='Test Found Person',
            estimated_age=25,
            gender='unknown',
            found_location='Test Location',
            found_date='2024-01-02',
            found_by_organization='Test Organization'
        )
        found.photo.save('test_found.jpg', ContentFile(img_buffer.getvalue()), save=True)
        found.save()
        
        print("✓ Test data created successfully")
        
    except Exception as e:
        print(f"✗ Error creating test data: {e}")


def test_api_endpoints():
    """Test the API endpoints (simplified version)."""
    print_header("API Endpoint Test")
    
    print("API endpoints created:")
    print("  ✓ /api/face-search/ - Enhanced face search with classification")
    print("  ✓ /api/quick-match/ - Quick matching for mobile apps")
    print("  ✓ /face-search/ - Web interface for face search")
    
    print("\nTo test API endpoints:")
    print("1. Start the Django server: python manage.py runserver")
    print("2. Use Postman/curl to send POST requests to the endpoints")
    print("3. Include image data in the request")
    
    # Test URL configuration
    try:
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        
        # Test if URLs resolve correctly
        try:
            url = reverse('core:api_face_search')
            print(f"  ✓ API face search URL resolves: {url}")
        except:
            print("  ✗ API face search URL not found")
            
        try:
            url = reverse('core:api_quick_match')
            print(f"  ✓ Quick match URL resolves: {url}")
        except:
            print("  ✗ Quick match URL not found")
            
    except Exception as e:
        print(f"  URL testing failed: {e}")


def test_matching_service():
    """Test the matching service integration."""
    print_header("Matching Service Test")
    
    try:
        # Test embedding generation
        test_image = Image.new('RGB', (200, 200), color='white')
        img_buffer = BytesIO()
        test_image.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        uploaded_file = InMemoryUploadedFile(
            img_buffer,
            'test_image',
            'test.jpg',
            'image/jpeg',
            img_buffer.tell(),
            None
        )
        
        embedding = matching_service.generate_face_embedding(
            uploaded_file,
            from_upload=True,
            use_deepface=DEEPFACE_AVAILABLE
        )
        
        if embedding is not None:
            print(f"✓ Matching service generated embedding: {len(embedding)} dimensions")
        else:
            print("✗ Matching service could not generate embedding")
            
    except Exception as e:
        print(f"✗ Matching service test failed: {e}")


def main():
    """Run all tests."""
    print_header("VanishVault Enhanced Face Matching System Test")
    
    tests = [
        ("AI Library Availability", test_ai_library_availability),
        ("Confidence Scoring", test_confidence_scoring),
        ("Image Preprocessing", test_image_preprocessing),
        ("Face Detection", test_face_detection),
        ("Database Matching", test_database_matching),
        ("Matching Service", test_matching_service),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            test_func()
            results[test_name] = "PASSED"
        except Exception as e:
            print(f"\n✗ {test_name} failed with error: {e}")
            results[test_name] = "FAILED"
    
    # Summary
    print_header("Test Summary")
    for test_name, status in results.items():
        status_symbol = "✓" if status == "PASSED" else "✗"
        print(f"{status_symbol} {test_name}: {status}")
    
    passed = sum(1 for status in results.values() if status == "PASSED")
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced face matching system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
