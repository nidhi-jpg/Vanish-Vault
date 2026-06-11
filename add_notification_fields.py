#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from django.db import connection

def add_notification_fields():
    """Manually add missing fields to notification table"""
    cursor = connection.cursor()
    
    print("Adding missing fields to core_notification table...")
    
    # Add sender field
    try:
        cursor.execute('ALTER TABLE core_notification ADD COLUMN sender_id INTEGER NULL REFERENCES core_user(id);')
        print('✓ Added sender field')
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print('✓ Sender field already exists')
        else:
            print(f'✗ Sender field error: {e}')

    # Add priority field
    try:
        cursor.execute('ALTER TABLE core_notification ADD COLUMN priority VARCHAR(10) DEFAULT "medium";')
        print('✓ Added priority field')
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print('✓ Priority field already exists')
        else:
            print(f'✗ Priority field error: {e}')

    # Add data field
    try:
        cursor.execute('ALTER TABLE core_notification ADD COLUMN data TEXT DEFAULT "{}";')
        print('✓ Added data field')
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print('✓ Data field already exists')
        else:
            print(f'✗ Data field error: {e}')

    # Add is_email_sent field
    try:
        cursor.execute('ALTER TABLE core_notification ADD COLUMN is_email_sent BOOLEAN DEFAULT FALSE;')
        print('✓ Added is_email_sent field')
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print('✓ is_email_sent field already exists')
        else:
            print(f'✗ is_email_sent field error: {e}')

    # Add expires_at field
    try:
        cursor.execute('ALTER TABLE core_notification ADD COLUMN expires_at DATETIME NULL;')
        print('✓ Added expires_at field')
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print('✓ expires_at field already exists')
        else:
            print(f'✗ expires_at field error: {e}')
    
    print("\nField additions completed!")

if __name__ == '__main__':
    add_notification_fields()
