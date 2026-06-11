#!/usr/bin/env python
"""Check dashboard HTML output"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import MissingPerson, FoundPerson, PotentialMatch, User
from django.test import Client
from django.contrib.messages.storage.fallback import FallbackStorage

User = get_user_model()

def check_dashboard_html():
    print("Checking Dashboard HTML Output")
    print("=" * 50)
    
    # Get admin user
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        print("❌ Admin user not found!")
        return
    
    # Create client and login
    client = Client()
    login_success = client.login(username='admin', password='admin123')
    
    if not login_success:
        print("❌ Failed to login as admin")
        return
    
    # Get dashboard page
    response = client.get('/dashboard/')
    
    if response.status_code != 200:
        print(f"❌ Dashboard failed: {response.status_code}")
        return
    
    # Get HTML content
    html_content = response.content.decode('utf-8')
    
    print("\n✅ Dashboard loaded successfully")
    
    # Check for key elements
    checks = [
        ('Admin Dashboard', 'Dashboard title'),
        ('Statistics Overview', 'Stats section'),
        ('Pending Missing Cases', 'Missing cases section'),
        ('Unidentified Found Persons', 'Found cases section'),
        ('User Management', 'User management section'),
        ('AI Face Matches', 'AI matches section'),
        ('Test Missing Person', 'Test missing case data'),
        ('John Doe', 'Test found case data'),
        ('test_police', 'Test user data'),
    ]
    
    print("\n📋 Checking Dashboard Elements:")
    for text, description in checks:
        if text in html_content:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} - Missing '{text}'")
    
    # Check for specific data counts
    print("\n📊 Checking Data Display:")
    
    # Count pending missing cases in HTML
    import re
    pending_missing_count = len(re.findall(r'MP-\d{4}-\w{5}', html_content))
    print(f"   Pending missing cases displayed: {pending_missing_count}")
    
    # Count found persons in HTML
    found_person_count = len(re.findall(r'FP-\d{4}-\w{5}', html_content))
    print(f"   Found persons displayed: {found_person_count}")
    
    # Check for user verification section
    if 'test_police' in html_content or 'test_ngo' in html_content:
        print("   ✅ User verification section present")
    else:
        print("   ❌ User verification section missing")
    
    # Save HTML to file for manual inspection
    with open('dashboard_output.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\n💾 Dashboard HTML saved to 'dashboard_output.html'")
    print("   Open this file in a browser to view the dashboard")
    
    print("\n" + "=" * 50)
    print("Dashboard HTML check completed!")

if __name__ == "__main__":
    check_dashboard_html()
