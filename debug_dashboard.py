#!/usr/bin/env python
"""Debug dashboard data"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import MissingPerson, FoundPerson, PotentialMatch, User
from core.views import dashboard
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

User = get_user_model()

def debug_dashboard():
    print("Debug Dashboard Data")
    print("=" * 50)
    
    # Get admin user
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        print("❌ Admin user not found!")
        return
    
    # Create request
    factory = RequestFactory()
    request = factory.get('/dashboard/')
    request.user = admin_user
    
    # Add messages support
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    # Call dashboard view
    print("\nCalling dashboard view...")
    try:
        response = dashboard(request)
        print(f"✅ Dashboard view executed successfully")
        print(f"   Response status: {response.status_code}")
        
        # Force template rendering to get context
        if hasattr(response, 'render'):
            response.render()
        
        # Check context data
        if hasattr(response, 'context_data') and response.context_data:
            context = response.context_data
            print(f"\n📊 Dashboard Context Data:")
            print(f"   Total found: {stats.get('total_found', 0)}")
            print(f"   Unidentified found: {stats.get('unidentified_found', 0)}")
            
            # Pending items
            pending_users = context.get('pending_users', [])
            pending_missing = context.get('pending_missing_cases', [])
            pending_found = context.get('pending_found_cases', [])
            pending_matches = context.get('pending_matches', [])
            
            print(f"\n   Pending users: {len(pending_users)}")
            for user in pending_users[:3]:
                print(f"     - {user.username} ({user.get_role_display()})")
            
            print(f"\n   Pending missing cases: {len(pending_missing)}")
            for case in pending_missing[:3]:
                print(f"     - {case.full_name} ({case.case_id}) - {case.get_status_display()}")
            
            print(f"\n   Pending found cases: {len(pending_found)}")
            for case in pending_found[:3]:
                name = case.possible_name or "Unidentified"
                print(f"     - {name} ({case.case_id}) - {case.get_status_display()}")
            
            print(f"\n   Pending AI matches: {len(pending_matches)}")
            for match in pending_matches[:3]:
                print(f"     - Match #{match.id} ({match.confidence}% confidence)")
        else:
            print("❌ No context data in response")
            
    except Exception as e:
        print(f"❌ Dashboard view error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_dashboard()
