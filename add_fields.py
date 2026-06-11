import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vanishvault.settings')
django.setup()

from django.db import connection

def add_fields():
    cursor = connection.cursor()
    
    print('Adding missing fields...')
    
    try:
        cursor.execute('ALTER TABLE core_notification ADD COLUMN priority VARCHAR(10) DEFAULT "medium"')
        print('✓ Added priority')
    except Exception as e:
        print(f'Priority: {e}')
    
    try:
        cursor.execute('ALTER TABLE core_notification ADD COLUMN sender_id INTEGER NULL REFERENCES core_user(id)')
        print('✓ Added sender')
    except Exception as e:
        print(f'Sender: {e}')
    
    print('Done!')

if __name__ == '__main__':
    add_fields()
