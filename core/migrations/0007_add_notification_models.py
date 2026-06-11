"""
Add notification system models
"""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20260224_1958'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('case_submitted', 'Case Submitted'), ('case_verified', 'Case Verified'), ('case_rejected', 'Case Rejected'), ('case_updated', 'Case Updated'), ('sighting_reported', 'Sighting Reported'), ('face_search_performed', 'Face Search Performed'), ('high_confidence_match', 'High Confidence Match'), ('police_assigned', 'Police Assigned'), ('system_alert', 'System Alert')], help_text='Type of notification', max_length=30)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', help_text='Priority level of this notification', max_length=10)),
                ('title', models.CharField(help_text='Notification title', max_length=200)),
                ('message', models.TextField(help_text='Detailed notification message')),
                ('data', models.JSONField(blank=True, default=dict, help_text='Additional notification data (e.g., match scores, rejection reasons)')),
                ('is_read', models.BooleanField(default=False, help_text='Whether the notification has been read')),
                ('is_email_sent', models.BooleanField(default=False, help_text='Whether email notification was sent')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the notification was created')),
                ('read_at', models.DateTimeField(blank=True, help_text='When the notification was read', null=True)),
                ('expires_at', models.DateTimeField(blank=True, help_text='When the notification expires (optional)', null=True)),
                ('missing_person', models.ForeignKey(blank=True, help_text='Related missing person case (if applicable)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='core.missingperson')),
                ('recipient', models.ForeignKey(help_text='User who receives this notification', on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='core.user')),
                ('sender', models.ForeignKey(blank=True, help_text='User who triggered this notification (if applicable)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_notifications', to='core.user')),
                ('sighting', models.ForeignKey(blank=True, help_text='Related sighting (if applicable)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='core.sighting')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('case_submitted', 'Case Submitted'), ('case_verified', 'Case Verified'), ('case_rejected', 'Case Rejected'), ('case_updated', 'Case Updated'), ('sighting_reported', 'Sighting Reported'), ('face_search_performed', 'Face Search Performed'), ('high_confidence_match', 'High Confidence Match'), ('police_assigned', 'Police Assigned'), ('system_alert', 'System Alert')], help_text='Notification type this template is for', max_length=30, unique=True)),
                ('subject_template', models.CharField(help_text='Email subject template (use Django template syntax)', max_length=200)),
                ('body_template', models.TextField(help_text='Email body template (use Django template syntax)')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this template is active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['notification_type'],
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_case_submitted', models.BooleanField(default=True)),
                ('email_case_verified', models.BooleanField(default=True)),
                ('email_case_rejected', models.BooleanField(default=True)),
                ('email_case_updated', models.BooleanField(default=True)),
                ('email_sighting_reported', models.BooleanField(default=True)),
                ('email_face_search', models.BooleanField(default=True)),
                ('email_high_confidence', models.BooleanField(default=True)),
                ('app_case_submitted', models.BooleanField(default=True)),
                ('app_case_verified', models.BooleanField(default=True)),
                ('app_case_rejected', models.BooleanField(default=True)),
                ('app_case_updated', models.BooleanField(default=True)),
                ('app_sighting_reported', models.BooleanField(default=True)),
                ('app_face_search', models.BooleanField(default=True)),
                ('app_high_confidence', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to='core.user')),
            ],
            options={
                'ordering': ['user'],
            },
        ),
        migrations.CreateModel(
            name='FaceSearchLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_image', models.ImageField(help_text='Image used for face search', upload_to='face_searches/')),
                ('match_score', models.FloatField(blank=True, help_text='Best match score (0.0 to 1.0)', null=True)),
                ('search_results', models.JSONField(blank=True, default=dict, help_text='Complete search results data')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of the searcher', null=True)),
                ('user_agent', models.TextField(blank=True, help_text='Browser user agent')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('matched_person', models.ForeignKey(blank=True, help_text='Person that was matched (if any)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='face_search_matches', to='core.missingperson')),
                ('missing_person', models.ForeignKey(help_text='Missing person being searched for', on_delete=django.db.models.deletion.CASCADE, related_name='face_searches', to='core.missingperson')),
                ('performed_by', models.ForeignKey(help_text='User who performed the face search', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='face_searches', to='core.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read'], name='core_notification_recipient_is__idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['notification_type'], name='core_notification_notificati_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['priority'], name='core_notification_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['created_at'], name='core_notification_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='facesearchlog',
            index=models.Index(fields=['performed_by'], name='core_facesearchlog_performed_idx'),
        ),
        migrations.AddIndex(
            model_name='facesearchlog',
            index=models.Index(fields=['missing_person'], name='core_facesearchlog_missing_p_idx'),
        ),
        migrations.AddIndex(
            model_name='facesearchlog',
            index=models.Index(fields=['match_score'], name='core_facesearchlog_match_scor_idx'),
        ),
        migrations.AddIndex(
            model_name='facesearchlog',
            index=models.Index(fields=['created_at'], name='core_facesearchlog_created__idx'),
        ),
    ]
