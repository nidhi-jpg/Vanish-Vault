from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, MissingPerson, FoundPerson, Sighting, 
    VerificationTask, Notification, AuditLog, Photo
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin interface for custom User model"""
    
    list_display = [
        'username', 'email', 'full_name', 'role', 'organization', 
        'phone_verified', 'is_verified', 'is_active', 'date_joined'
    ]
    
    list_filter = [
        'role', 'phone_verified', 'is_verified', 'is_active', 
        'is_staff', 'date_joined'
    ]
    
    search_fields = ['username', 'email', 'first_name', 'last_name', 'organization']
    
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Role & Organization', {
            'fields': ('role', 'organization', 'id_document')
        }),
        ('Verification', {
            'fields': (
                'phone_verified', 'is_verified', 'verified_by', 'verified_at', 'verification_notes'
            )
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    full_name.short_description = 'Full Name'

    actions = ['verify_selected_users']

    def verify_selected_users(self, request, queryset):
        """Admin action to mark users as verified and log an AuditLog entry"""
        updated = 0
        for user in queryset:
            if not user.is_verified:
                user.is_verified = True
                user.verified_by = request.user if request.user.is_authenticated else None
                user.verified_at = timezone.now()
                user.save()
                # Create AuditLog
                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='verify',
                    model_name='User',
                    object_id=str(user.pk),
                    details=f'User {user.username} verified via admin action.'
                )
                updated += 1
        self.message_user(request, f"Verified {updated} user(s).")
    verify_selected_users.short_description = 'Verify selected users'


@admin.register(MissingPerson)
class MissingPersonAdmin(admin.ModelAdmin):
    """Admin interface for MissingPerson model"""
    
    list_display = [
        'case_id', 'full_name', 'age', 'gender', 'last_seen_location', 
        'last_seen_date', 'status', 'reporter', 'days_missing', 'created_at'
    ]
    
    list_filter = [
        'status', 'gender', 'created_at', 'last_seen_date', 'verified_at'
    ]
    
    search_fields = [
        'case_id', 'full_name', 'last_seen_location', 'description',
        'reporter__username', 'reporter__first_name', 'reporter__last_name'
    ]
    
    readonly_fields = ['case_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Case Information', {
            'fields': ('case_id', 'status', 'created_at', 'updated_at')
        }),
        ('Person Details', {
            'fields': (
                'full_name', 'age', 'gender', 'height', 'weight',
                'hair_color', 'eye_color', 'distinguishing_features'
            )
        }),
        ('Disappearance', {
            'fields': (
                'last_seen_location', 'last_seen_date', 'last_seen_time', 'description'
            )
        }),
        ('Media', {
            'fields': ('photo', 'additional_photos')
        }),
        ('Reporter Information', {
            'fields': (
                'reporter', 'reporter_relationship', 'reporter_phone'
            )
        }),
        ('Verification', {
            'fields': ('verified_at', 'verified_by')
        }),
    )
    
    ordering = ['-created_at']
    
    def days_missing(self, obj):
        days = obj.days_missing
        if days is not None:
            if days == 0:
                return "Today"
            elif days == 1:
                return "1 day"
            else:
                return f"{days} days"
        return "Unknown"
    days_missing.short_description = 'Days Missing'


@admin.register(FoundPerson)
class FoundPersonAdmin(admin.ModelAdmin):
    """Admin interface for FoundPerson model"""
    
    list_display = [
        'case_id', 'possible_name', 'estimated_age', 'gender', 
        'found_location', 'found_date', 'status', 'found_by_organization'
    ]
    
    list_filter = ['status', 'gender', 'found_date', 'created_at']
    
    search_fields = [
        'case_id', 'possible_name', 'found_location', 'notes',
        'found_by_organization', 'contact_person'
    ]
    
    readonly_fields = ['case_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Case Information', {
            'fields': ('case_id', 'status', 'created_at', 'updated_at')
        }),
        ('Person Details', {
            'fields': (
                'possible_name', 'estimated_age', 'gender', 'height', 'weight',
                'hair_color', 'eye_color', 'distinguishing_features'
            )
        }),
        ('Found Details', {
            'fields': (
                'found_location', 'found_date', 'found_time', 'notes'
            )
        }),
        ('Media', {
            'fields': ('photo', 'additional_photos')
        }),
        ('Organization', {
            'fields': (
                'found_by_organization', 'contact_person', 'contact_phone'
            )
        }),
        ('Identification', {
            'fields': ('identified_at',)
        }),
    )
    
    ordering = ['-created_at']


@admin.register(Sighting)
class SightingAdmin(admin.ModelAdmin):
    """Admin interface for Sighting model"""
    
    list_display = [
        'missing_person', 'location', 'date', 'time', 'confidence_level',
        'status', 'reporter_name', 'created_at'
    ]
    
    list_filter = ['status', 'confidence_level', 'date', 'created_at']
    
    search_fields = [
        'missing_person__full_name', 'location', 'description',
        'reporter_name', 'reporter_phone'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Sighting Details', {
            'fields': (
                'missing_person', 'location', 'date', 'time', 'description',
                'confidence_level'
            )
        }),
        ('Reporter Information', {
            'fields': (
                'reporter', 'reporter_name', 'reporter_phone', 'reporter_email'
            )
        }),
        ('Status', {
            'fields': ('status', 'verified_by', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    ordering = ['-created_at']


@admin.register(VerificationTask)
class VerificationTaskAdmin(admin.ModelAdmin):
    """Admin interface for VerificationTask model"""
    
    list_display = [
        'task_type', 'priority', 'status', 'assigned_to', 
        'related_case', 'due_date', 'created_at'
    ]
    
    list_filter = ['task_type', 'priority', 'status', 'created_at']
    
    search_fields = [
        'description', 'assigned_to__username', 'related_case__full_name',
        'related_sighting__missing_person__full_name'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('task_type', 'priority', 'status', 'description')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'due_date')
        }),
        ('Related Items', {
            'fields': ('related_case', 'related_sighting')
        }),
        ('Progress', {
            'fields': ('notes', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    ordering = ['-priority', '-created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model"""
    
    list_display = [
        'user', 'notification_type', 'title', 'is_read', 'created_at'
    ]
    
    list_filter = ['notification_type', 'is_read', 'created_at']
    
    search_fields = [
        'user__username', 'title', 'message'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Notification', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Related Items', {
            'fields': ('related_case', 'related_sighting')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    ordering = ['-created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model"""
    
    list_display = [
        'action', 'model_name', 'object_id', 'user', 'ip_address', 'created_at'
    ]
    
    list_filter = ['action', 'model_name', 'created_at']
    
    search_fields = [
        'user__username', 'model_name', 'object_id', 'details'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Action Details', {
            'fields': ('action', 'model_name', 'object_id', 'details')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    ordering = ['-created_at']


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """Admin interface for Photo model"""
    
    list_display = ['caption', 'uploaded_by', 'uploaded_at', 'image_preview']
    
    list_filter = ['uploaded_at']
    
    search_fields = ['caption', 'uploaded_by__username']
    
    readonly_fields = ['uploaded_at', 'image_preview']
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('image', 'caption', 'uploaded_by')
        }),
        ('Preview', {
            'fields': ('image_preview',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',)
        }),
    )
    
    ordering = ['-uploaded_at']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


# Admin site customization
admin.site.site_header = "VanishVault Administration"
admin.site.site_title = "VanishVault Admin"
admin.site.index_title = "Welcome to VanishVault Administration"

# Add dashboard link to admin
from django.urls import reverse
from django.utils.html import format_html

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        return urls

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Add dashboard link
        if request.user.is_authenticated and (request.user.is_staff or request.user.role == User.Roles.ADMIN):
            extra_context['dashboard_url'] = reverse('core:dashboard')
        return super().index(request, extra_context)

# Override the default admin site
admin.site = CustomAdminSite(name='admin')

# Re-register all models
admin.site.register(User, CustomUserAdmin)
admin.site.register(MissingPerson, MissingPersonAdmin)
admin.site.register(FoundPerson, FoundPersonAdmin)
admin.site.register(Sighting, SightingAdmin)
admin.site.register(VerificationTask, VerificationTaskAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
admin.site.register(Photo, PhotoAdmin)