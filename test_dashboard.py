#!/usr/bin/env python
"""Test dashboard functionality"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from core.models import MissingPerson, FoundPerson, PotentialMatch, User

User = get_user_model()

def test_dashboard():
    print("Testing Dashboard Functionality")
    print("=" * 50)
    
    # Get admin user
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        print("❌ Admin user not found!")
        return
    
    # Create client and login
    client = Client()
    login_success = client.login(username='admin', password='admin123')
    print(f"   Login success: {login_success}")
    
    if not login_success:
        print("❌ Failed to login as admin")
        return
    
    # Test dashboard access
    print("\n1. Testing dashboard access...")
    response = client.get('/dashboard/')
    print(f"   Response status: {response.status_code}")
    print(f"   Response content type: {response.get('Content-Type')}")
    
    if response.status_code == 200:
        print("✅ Dashboard accessible (200 OK)")
        # Check if it's the dashboard template
        if 'Admin Dashboard' in response.content.decode():
            print("✅ Dashboard template rendered")
        else:
            print("⚠️ Response may not be dashboard template")
    elif response.status_code == 302:
        print(f"ℹ️ Dashboard redirected to: {response.url}")
        # Follow redirect
        response = client.get(response.url)
        if response.status_code == 200:
            print("✅ Dashboard accessible after redirect")
        else:
            print(f"❌ Dashboard failed after redirect: {response.status_code}")
    else:
        print(f"❌ Dashboard access failed: {response.status_code}")
        return
    
    # Check context data
    print("\n2. Checking dashboard context data...")
    context = response.context
    
    if not context:
        print("❌ No context data available")
        return
    
    # Check stats
    stats = context.get('stats', {})
    print(f"   Total users: {stats.get('total_users', 0)}")
    print(f"   Verified users: {stats.get('verified_users', 0)}")
    print(f"   Pending missing cases: {stats.get('pending_missing', 0)}")
    print(f"   Unidentified found persons: {stats.get('unidentified_found', 0)}")
    
    # Check pending items
    pending_users = context.get('pending_users', [])
    pending_missing = context.get('pending_missing_cases', [])
    pending_found = context.get('pending_found_cases', [])
    pending_matches = context.get('pending_matches', [])
    
    print(f"\n   Pending users: {len(pending_users)}")
    print(f"   Pending missing cases: {len(pending_missing)}")
    print(f"   Pending found cases: {len(pending_found)}")
    print(f"   Pending AI matches: {len(pending_matches)}")
    
    # Test individual tabs
    print("\n3. Testing dashboard components...")
    
    # Show pending missing cases
    if pending_missing:
        print(f"\n   Pending Missing Cases:")
        for case in pending_missing[:3]:  # Show first 3
            print(f"   - {case.full_name} ({case.case_id}) - {case.get_status_display()}")
    
    # Show pending found cases
    if pending_found:
        print(f"\n   Pending Found Cases:")
        for case in pending_found[:3]:  # Show first 3
            name = case.possible_name or "Unidentified"
            print(f"   - {name} ({case.case_id}) - {case.get_status_display()}")
    
    # Show pending users
    if pending_users:
        print(f"\n   Pending User Verifications:")
        for user in pending_users[:3]:  # Show first 3
            print(f"   - {user.username} ({user.get_role_display()})")
    
    # Test dashboard URLs
    print("\n4. Testing dashboard URLs...")
    urls_to_test = [
        ('/dashboard/', 'Dashboard'),
        ('/admin/user/1/verify/', 'Verify User'),
        ('/admin/missing/1/verify/', 'Verify Missing Case'),
        ('/admin/found/1/verify/', 'Verify Found Case'),
    ]
    
    for url, name in urls_to_test:
        response = client.get(url)
        if response.status_code in [200, 405]:  # 405 for POST-only views
            print(f"   ✅ {name}: {response.status_code}")
        else:
            print(f"   ❌ {name}: {response.status_code}")
    
    # Test role-based access
    print("\n5. Testing role-based access...")
    
    # Test with regular citizen
    citizen = User.objects.filter(role=User.Roles.CITIZEN).first()
    if citizen:
        client.logout()
        client.login(username=citizen.username, password='test123')
        response = client.get('/dashboard/')
        if response.status_code == 302:  # Should redirect
            print("   ✅ Citizen correctly redirected from dashboard")
        else:
            print(f"   ❌ Citizen access not restricted: {response.status_code}")
    
    # Test with unverified police
    police = User.objects.filter(role=User.Roles.POLICE, is_verified=False).first()
    if police:
        client.logout()
        client.login(username=police.username, password='test123')
        response = client.get('/dashboard/')
        if response.status_code == 302:  # Should redirect
            print("   ✅ Unverified police correctly redirected from dashboard")
        else:
            print(f"   ❌ Unverified police access not restricted: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("Dashboard test completed!")
    print("\nTo manually test:")
    print("1. Go to http://127.0.0.1:8000/login/")
    print("2. Login with admin/admin123")
    print("3. You should be redirected to /dashboard/")

if __name__ == "__main__":
    test_dashboard()
