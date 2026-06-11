#!/usr/bin/env python
"""
VanishVault Testing Dashboard - Interactive testing progress tracker.
Helps you systematically test all features and track your progress.
"""

import os
import sys
import django
import json
from datetime import datetime
from typing import Dict, List, Any

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()


class TestingDashboard:
    """Interactive testing dashboard for VanishVault."""
    
    def __init__(self):
        self.test_data_file = "testing_progress.json"
        self.load_test_data()
        
    def load_test_data(self):
        """Load existing test progress or create new."""
        try:
            with open(self.test_data_file, 'r') as f:
                self.test_data = json.load(f)
        except FileNotFoundError:
            self.test_data = self.initialize_test_data()
            self.save_test_data()
    
    def save_test_data(self):
        """Save test progress to file."""
        with open(self.test_data_file, 'w') as f:
            json.dump(self.test_data, f, indent=2)
    
    def initialize_test_data(self):
        """Initialize comprehensive test data structure."""
        return {
            'test_session': {
                'started_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_features': 0,
                'tested_features': 0,
                'passed_features': 0,
                'failed_features': 0
            },
            'roles': {
                'public': {
                    'name': 'Public (No Login)',
                    'description': 'Features accessible without authentication',
                    'features': {
                        'home_page': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'search_page': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'missing_list': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'found_list': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'login_page': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'register_page': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'about_page': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'contact_page': {'status': 'pending', 'notes': '', 'tested_at': None}
                    }
                },
                'citizen': {
                    'name': 'Citizen',
                    'description': 'Regular user with basic reporting capabilities',
                    'credentials': 'citizen_test / CitizenTest123!',
                    'features': {
                        'login': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'dashboard': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'profile_management': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'report_missing': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'report_found': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'face_search': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'contact_request': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'sighting_report': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'case_tracking': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'notifications': {'status': 'pending', 'notes': '', 'tested_at': None}
                    }
                },
                'police': {
                    'name': 'Police Officer',
                    'description': 'Law enforcement with verification powers',
                    'credentials': 'police_test / PoliceTest123!',
                    'features': {
                        'login': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'dashboard': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'case_verification': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'advanced_search': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'contact_info_access': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'match_review': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'user_verification': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'reports_generation': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'audit_logs': {'status': 'pending', 'notes': '', 'tested_at': None}
                    }
                },
                'ngo': {
                    'name': 'NGO Worker',
                    'description': 'Non-profit organization worker',
                    'credentials': 'ngo_test / NgoTest123!',
                    'features': {
                        'login': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'dashboard': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'bulk_reporting': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'volunteer_management': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'organization_cases': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'coordination_tools': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'resource_management': {'status': 'pending', 'notes': '', 'tested_at': None}
                    }
                },
                'admin': {
                    'name': 'Administrator',
                    'description': 'System administrator with full access',
                    'credentials': 'admin_test / AdminTest123!',
                    'features': {
                        'login': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'dashboard': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'user_management': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'role_assignment': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'system_settings': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'security_monitoring': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'backup_restore': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'content_management': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'database_management': {'status': 'pending', 'notes': '', 'tested_at': None},
                        'api_management': {'status': 'pending', 'notes': '', 'tested_at': None}
                    }
                }
            },
            'integration_tests': {
                'name': 'Integration Tests',
                'description': 'Cross-functional testing scenarios',
                'features': {
                    'email_notifications': {'status': 'pending', 'notes': '', 'tested_at': None},
                    'file_uploads': {'status': 'pending', 'notes': '', 'tested_at': None},
                    'face_matching_ai': {'status': 'pending', 'notes': '', 'tested_at': None},
                    'api_endpoints': {'status': 'pending', 'notes': '', 'tested_at': None},
                    'mobile_compatibility': {'status': 'pending', 'notes': '', 'tested_at': None},
                    'security_features': {'status': 'pending', 'notes': '', 'tested_at': None},
                    'performance_tests': {'status': 'pending', 'notes': '', 'tested_at': None},
                    'error_handling': {'status': 'pending', 'notes': '', 'tested_at': None}
                }
            }
        }
    
    def print_header(self, title):
        """Print formatted header."""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
    
    def print_subheader(self, title):
        """Print formatted subheader."""
        print(f"\n{'-'*60}")
        print(f"  {title}")
        print(f"{'-'*60}")
    
    def show_main_menu(self):
        """Display main menu options."""
        self.print_header("VanishVault Testing Dashboard")
        
        # Calculate overall progress
        total_features = 0
        tested_features = 0
        passed_features = 0
        
        for category in ['roles', 'integration_tests']:
            for section in self.test_data[category].values():
                if 'features' in section:
                    for feature in section['features'].values():
                        total_features += 1
                        if feature['status'] != 'pending':
                            tested_features += 1
                        if feature['status'] == 'passed':
                            passed_features += 1
        
        progress = (tested_features / total_features * 100) if total_features > 0 else 0
        success_rate = (passed_features / tested_features * 100) if tested_features > 0 else 0
        
        print(f"📊 Overall Progress: {progress:.1f}% ({tested_features}/{total_features} features tested)")
        print(f"✅ Success Rate: {success_rate:.1f}% ({passed_features}/{tested_features} passed)")
        print(f"🕐 Last Updated: {self.test_data['test_session']['last_updated']}")
        
        print("\n🎯 Main Menu:")
        print("1. 📋 View Testing Progress")
        print("2. 👤 Test Specific Role")
        print("3. 🔧 Test Integration Features")
        print("4. 📊 View Summary Report")
        print("5. 📝 Add Test Notes")
        print("6. 🔄 Reset Progress")
        print("7. 🚪 Exit")
        
        choice = input("\nSelect an option (1-7): ").strip()
        return choice
    
    def view_testing_progress(self):
        """Show detailed testing progress."""
        self.print_header("Testing Progress Overview")
        
        for category_name, category in self.test_data.items():
            if category_name == 'test_session':
                continue
                
            self.print_subheader(category['name'])
            print(f"📝 {category['description']}")
            
            if 'credentials' in category:
                print(f"🔑 Credentials: {category['credentials']}")
            
            for feature_name, feature_data in category['features'].items():
                status_icon = self.get_status_icon(feature_data['status'])
                notes = f" - {feature_data['notes']}" if feature_data['notes'] else ""
                tested_time = f" (tested: {feature_data['tested_at']})" if feature_data['tested_at'] else ""
                print(f"  {status_icon} {feature_name.replace('_', ' ').title()}{notes}{tested_time}")
    
    def test_specific_role(self):
        """Interactive testing for a specific role."""
        self.print_header("Test Specific Role")
        
        print("Available roles:")
        roles = list(self.test_data['roles'].keys())
        for i, role_key in enumerate(roles, 1):
            role = self.test_data['roles'][role_key]
            print(f"{i}. {role['name']}")
        
        choice = input(f"\nSelect role (1-{len(roles)}): ").strip()
        
        try:
            role_index = int(choice) - 1
            if 0 <= role_index < len(roles):
                role_key = roles[role_index]
                self.interactive_role_testing(role_key)
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def interactive_role_testing(self, role_key):
        """Interactive testing for selected role."""
        role = self.test_data['roles'][role_key]
        
        self.print_subheader(f"Testing: {role['name']}")
        print(f"📝 {role['description']}")
        if 'credentials' in role:
            print(f"🔑 Login with: {role['credentials']}")
        
        features = list(role['features'].keys())
        
        while True:
            print(f"\n🧪 Features to test:")
            for i, feature_name in enumerate(features, 1):
                feature_data = role['features'][feature_name]
                status_icon = self.get_status_icon(feature_data['status'])
                print(f"{i}. {status_icon} {feature_name.replace('_', ' ').title()}")
            
            print(f"{len(features)+1}. 📊 Return to main menu")
            
            choice = input(f"\nSelect feature to test (1-{len(features)+1}): ").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(features):
                    feature_name = features[choice_num - 1]
                    self.test_feature(role_key, feature_name)
                elif choice_num == len(features) + 1:
                    break
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
    
    def test_feature(self, role_key, feature_name):
        """Interactive testing for a specific feature."""
        role = self.test_data['roles'][role_key]
        feature = role['features'][feature_name]
        
        self.print_subheader(f"Testing: {feature_name.replace('_', ' ').title()}")
        
        print(f"📝 Current Status: {feature['status']}")
        if feature['notes']:
            print(f"📝 Previous Notes: {feature['notes']}")
        
        print(f"\n🧪 Testing Instructions:")
        instructions = self.get_testing_instructions(role_key, feature_name)
        print(instructions)
        
        print(f"\n📋 Test Results:")
        print("1. ✅ Passed")
        print("2. ❌ Failed")
        print("3. ⚠️ Partial")
        print("4. 📝 Add Notes Only")
        print("5. 🔙 Back")
        
        choice = input("Select result (1-5): ").strip()
        
        if choice == '1':
            feature['status'] = 'passed'
            notes = input("Add notes (optional): ").strip()
            if notes:
                feature['notes'] = notes
            feature['tested_at'] = datetime.now().isoformat()
            print("✅ Marked as passed")
        elif choice == '2':
            feature['status'] = 'failed'
            notes = input("Describe the issue: ").strip()
            feature['notes'] = notes
            feature['tested_at'] = datetime.now().isoformat()
            print("❌ Marked as failed")
        elif choice == '3':
            feature['status'] = 'partial'
            notes = input("Describe what works and what doesn't: ").strip()
            feature['notes'] = notes
            feature['tested_at'] = datetime.now().isoformat()
            print("⚠️ Marked as partial")
        elif choice == '4':
            notes = input("Add notes: ").strip()
            if notes:
                feature['notes'] = notes
            print("📝 Notes added")
        elif choice == '5':
            return
        else:
            print("❌ Invalid selection")
            return
        
        self.test_data['test_session']['last_updated'] = datetime.now().isoformat()
        self.save_test_data()
    
    def get_testing_instructions(self, role_key, feature_name):
        """Get specific testing instructions for a feature."""
        instructions = {
            'public': {
                'home_page': "1. Go to http://localhost:8000/\n2. Verify page loads correctly\n3. Check navigation menu\n4. Test search functionality\n5. Verify content displays properly",
                'search_page': "1. Navigate to search page\n2. Test search with different terms\n3. Test filters (age, gender, location)\n4. Verify results display\n5. Check pagination if exists",
                'login_page': "1. Go to login page\n2. Verify form fields display\n3. Test validation (empty fields)\n4. Test with invalid credentials\n5. Check 'remember me' functionality",
                'register_page': "1. Go to registration page\n2. Fill form with valid data\n3. Test password requirements\n4. Test email validation\n5. Verify account creation"
            },
            'citizen': {
                'login': "1. Use credentials: citizen_test / CitizenTest123!\n2. Verify successful login\n3. Check redirect to dashboard\n4. Test logout functionality\n5. Verify session persistence",
                'dashboard': "1. Login as citizen\n2. Navigate to dashboard\n3. Verify personal info displays\n4. Check recent activity\n5. Test navigation to other features",
                'report_missing': "1. Click 'Report Missing Person'\n2. Fill all form fields\n3. Upload test photo\n4. Submit form\n5. Verify success message and case ID",
                'face_search': "1. Navigate to Face Search\n2. Upload clear face photo\n3. Run search against database\n4. Check confidence scores\n5. Verify match classification"
            },
            'police': {
                'login': "1. Use credentials: police_test / PoliceTest123!\n2. Verify police dashboard loads\n3. Check police-specific features\n4. Test access to verification tools\n5. Verify role permissions",
                'case_verification': "1. Access verification dashboard\n2. Find pending missing person cases\n3. Review case details\n4. Test approve/reject functionality\n5. Add verification notes",
                'advanced_search': "1. Use advanced search features\n2. Test filters for status, date ranges\n3. Search by case ID\n4. Access full case details\n5. Export search results"
            },
            'ngo': {
                'login': "1. Use credentials: ngo_test / NgoTest123!\n2. Verify NGO dashboard loads\n3. Check organization-specific features\n4. Test volunteer management\n5. Verify reporting capabilities",
                'bulk_reporting': "1. Test multiple found person reporting\n2. Use organization-specific fields\n3. Upload multiple photos\n4. Verify batch processing\n5. Check organization dashboard"
            },
            'admin': {
                'login': "1. Use credentials: admin_test / AdminTest123!\n2. Verify admin dashboard loads\n3. Check full system access\n4. Test user management access\n5. Verify system settings access",
                'user_management': "1. Access user management panel\n2. View all user accounts\n3. Test user creation\n4. Modify existing users\n5. Test role assignment",
                'system_settings': "1. Access system settings\n2. Modify configuration options\n3. Test security settings\n4. Check email configuration\n5. Verify backup settings"
            }
        }
        
        if role_key in instructions and feature_name in instructions[role_key]:
            return instructions[role_key][feature_name]
        else:
            return f"1. Access the {feature_name.replace('_', ' ').title()} feature\n2. Test all functionality\n3. Verify expected behavior\n4. Check for errors\n5. Document results"
    
    def test_integration_features(self):
        """Test integration and cross-functional features."""
        self.print_header("Integration Testing")
        
        features = list(self.test_data['integration_tests']['features'].keys())
        
        while True:
            print(f"\n🔗 Integration Features:")
            for i, feature_name in enumerate(features, 1):
                feature_data = self.test_data['integration_tests']['features'][feature_name]
                status_icon = self.get_status_icon(feature_data['status'])
                print(f"{i}. {status_icon} {feature_name.replace('_', ' ').title()}")
            
            print(f"{len(features)+1}. 🔙 Back to main menu")
            
            choice = input(f"\nSelect feature to test (1-{len(features)+1}): ").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(features):
                    feature_name = features[choice_num - 1]
                    self.test_integration_feature(feature_name)
                elif choice_num == len(features) + 1:
                    break
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
    
    def test_integration_feature(self, feature_name):
        """Test specific integration feature."""
        feature = self.test_data['integration_tests']['features'][feature_name]
        
        self.print_subheader(f"Testing: {feature_name.replace('_', ' ').title()}")
        
        instructions = {
            'email_notifications': "1. Trigger an email (registration, case update)\n2. Check email inbox\n3. Verify email content\n4. Test email formatting\n5. Check spam folder",
            'file_uploads': "1. Upload photos in different formats\n2. Test large file uploads\n3. Test invalid file types\n4. Check file size limits\n5. Verify file storage",
            'face_matching_ai': "1. Upload clear face photo\n2. Run AI face matching\n3. Check confidence scores\n4. Test with different angles\n5. Verify match accuracy",
            'api_endpoints': "1. Test /api/face-search/\n2. Test /api/quick-match/\n3. Verify JSON responses\n4. Test authentication\n5. Check rate limiting",
            'security_features': "1. Test login attempt limits\n2. Test session security\n3. Verify role permissions\n4. Test XSS protection\n5. Check CSRF protection"
        }
        
        print(f"📝 Current Status: {feature['status']}")
        print(f"🧪 Testing Instructions:\n{instructions.get(feature_name, 'Test the integration feature thoroughly')}")
        
        choice = input("\n📋 Test Result (1=Passed, 2=Failed, 3=Partial, 4=Notes): ").strip()
        
        status_map = {'1': 'passed', '2': 'failed', '3': 'partial'}
        if choice in status_map:
            feature['status'] = status_map[choice]
            notes = input("Add notes: ").strip()
            if notes:
                feature['notes'] = notes
            feature['tested_at'] = datetime.now().isoformat()
            self.save_test_data()
            print(f"✅ Status updated to {feature['status']}")
        elif choice == '4':
            notes = input("Add notes: ").strip()
            if notes:
                feature['notes'] = notes
                self.save_test_data()
                print("📝 Notes added")
    
    def view_summary_report(self):
        """Generate and display summary report."""
        self.print_header("Testing Summary Report")
        
        # Calculate statistics
        total_features = 0
        tested_features = 0
        passed_features = 0
        failed_features = 0
        partial_features = 0
        
        for category in ['roles', 'integration_tests']:
            for section in self.test_data[category].values():
                if 'features' in section:
                    for feature in section['features'].values():
                        total_features += 1
                        if feature['status'] == 'passed':
                            tested_features += 1
                            passed_features += 1
                        elif feature['status'] == 'failed':
                            tested_features += 1
                            failed_features += 1
                        elif feature['status'] == 'partial':
                            tested_features += 1
                            partial_features += 1
        
        progress = (tested_features / total_features * 100) if total_features > 0 else 0
        success_rate = (passed_features / tested_features * 100) if tested_features > 0 else 0
        
        print(f"📊 Overall Statistics:")
        print(f"  Total Features: {total_features}")
        print(f"  Tested Features: {tested_features}")
        print(f"  Passed: {passed_features}")
        print(f"  Failed: {failed_features}")
        print(f"  Partial: {partial_features}")
        print(f"  Progress: {progress:.1f}%")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Show failed features
        if failed_features > 0:
            print(f"\n❌ Failed Features:")
            for category in ['roles', 'integration_tests']:
                for section_name, section in self.test_data[category].items():
                    if 'features' in section:
                        for feature_name, feature_data in section['features'].items():
                            if feature_data['status'] == 'failed':
                                print(f"  - {section_name}: {feature_name}")
                                if feature_data['notes']:
                                    print(f"    Issue: {feature_data['notes']}")
        
        # Show next testing priorities
        print(f"\n🎯 Next Testing Priorities:")
        untested_count = 0
        for category in ['roles', 'integration_tests']:
            for section_name, section in self.test_data[category].items():
                if 'features' in section:
                    for feature_name, feature_data in section['features'].items():
                        if feature_data['status'] == 'pending':
                            if untested_count < 5:
                                print(f"  - {section_name}: {feature_name}")
                            untested_count += 1
        
        if untested_count > 5:
            print(f"  ... and {untested_count - 5} more features")
    
    def add_test_notes(self):
        """Add notes to any feature."""
        self.print_header("Add Test Notes")
        
        print("Select category:")
        print("1. 👤 User Roles")
        print("2. 🔗 Integration Tests")
        
        choice = input("Select category (1-2): ").strip()
        
        if choice == '1':
            self.add_role_notes()
        elif choice == '2':
            self.add_integration_notes()
        else:
            print("❌ Invalid selection")
    
    def add_role_notes(self):
        """Add notes to role features."""
        roles = list(self.test_data['roles'].keys())
        
        print("Select role:")
        for i, role_key in enumerate(roles, 1):
            role = self.test_data['roles'][role_key]
            print(f"{i}. {role['name']}")
        
        try:
            role_index = int(input("Select role: ").strip()) - 1
            if 0 <= role_index < len(roles):
                role_key = roles[role_index]
                role = self.test_data['roles'][role_key]
                
                features = list(role['features'].keys())
                print("Select feature:")
                for i, feature_name in enumerate(features, 1):
                    print(f"{i}. {feature_name.replace('_', ' ').title()}")
                
                feature_index = int(input("Select feature: ").strip()) - 1
                if 0 <= feature_index < len(features):
                    feature_name = features[feature_index]
                    notes = input("Enter notes: ").strip()
                    if notes:
                        role['features'][feature_name]['notes'] = notes
                        self.save_test_data()
                        print("📝 Notes added successfully")
                else:
                    print("❌ Invalid feature selection")
            else:
                print("❌ Invalid role selection")
        except ValueError:
            print("❌ Invalid input")
    
    def add_integration_notes(self):
        """Add notes to integration features."""
        features = list(self.test_data['integration_tests']['features'].keys())
        
        print("Select feature:")
        for i, feature_name in enumerate(features, 1):
            print(f"{i}. {feature_name.replace('_', ' ').title()}")
        
        try:
            feature_index = int(input("Select feature: ").strip()) - 1
            if 0 <= feature_index < len(features):
                feature_name = features[feature_index]
                notes = input("Enter notes: ").strip()
                if notes:
                    self.test_data['integration_tests']['features'][feature_name]['notes'] = notes
                    self.save_test_data()
                    print("📝 Notes added successfully")
            else:
                print("❌ Invalid feature selection")
        except ValueError:
            print("❌ Invalid input")
    
    def reset_progress(self):
        """Reset all testing progress."""
        self.print_header("Reset Testing Progress")
        
        confirm = input("⚠️  Are you sure you want to reset all progress? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            self.test_data = self.initialize_test_data()
            self.save_test_data()
            print("✅ All progress has been reset")
        else:
            print("❌ Reset cancelled")
    
    def get_status_icon(self, status):
        """Get icon for status."""
        icons = {
            'pending': '⏳',
            'passed': '✅',
            'failed': '❌',
            'partial': '⚠️'
        }
        return icons.get(status, '❓')
    
    def run(self):
        """Run the interactive dashboard."""
        print("🚀 Starting VanishVault Testing Dashboard...")
        print("📋 Make sure your server is running: python manage.py runserver")
        
        while True:
            choice = self.show_main_menu()
            
            if choice == '1':
                self.view_testing_progress()
            elif choice == '2':
                self.test_specific_role()
            elif choice == '3':
                self.test_integration_features()
            elif choice == '4':
                self.view_summary_report()
            elif choice == '5':
                self.add_test_notes()
            elif choice == '6':
                self.reset_progress()
            elif choice == '7':
                print("\n👋 Thank you for using VanishVault Testing Dashboard!")
                break
            else:
                print("❌ Invalid selection. Please try again.")
            
            input("\nPress Enter to continue...")


def main():
    """Main function to run the testing dashboard."""
    dashboard = TestingDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
