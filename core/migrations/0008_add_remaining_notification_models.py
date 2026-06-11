"""
Add remaining notification system models
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_add_notification_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('case_submitted', 'Case Submitted'), ('case_verified', 'Case Verified'), ('case_rejected', 'Case Rejected'), ('case_updated', 'Case Updated'), ('sighting_reported', 'Sighting Reported'), ('face_search_performed', 'Face Search Performed'), ('high_confidence_match', 'High Confidence Match'), ('police_assigned', 'Police Assigned'), ('system_alert', 'System Alert'), ('case_update', 'Case Update'), ('sighting_report', 'New Sighting'), ('verification_complete', 'Verification Complete'), ('system', 'System Message')], help_text='Notification type this template is for', max_length=30, unique=True)),
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
                ('search_results', models.TextField(blank=True, default='{}', help_text='Complete search results data (JSON format)')),
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
