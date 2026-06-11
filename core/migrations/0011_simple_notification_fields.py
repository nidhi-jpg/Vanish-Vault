"""
Add essential notification fields for SQLite compatibility
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_add_remaining_notification_models'),
    ]

    operations = [
        # Add sender field
        migrations.AddField(
            model_name='notification',
            name='sender',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='sent_notifications',
                to='core.user'
            ),
        ),
        
        # Add priority field
        migrations.AddField(
            model_name='notification',
            name='priority',
            field=models.CharField(
                choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')],
                default='medium',
                max_length=10
            ),
        ),
        
        # Add data field as TextField
        migrations.AddField(
            model_name='notification',
            name='data',
            field=models.TextField(
                blank=True,
                default='{}'
            ),
        ),
        
        # Add is_email_sent field
        migrations.AddField(
            model_name='notification',
            name='is_email_sent',
            field=models.BooleanField(
                default=False
            ),
        ),
        
        # Add expires_at field
        migrations.AddField(
            model_name='notification',
            name='expires_at',
            field=models.DateTimeField(
                blank=True,
                null=True
            ),
        ),
    ]
