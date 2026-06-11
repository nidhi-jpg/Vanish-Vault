"""
Audit logging models for VanishVault security and compliance.
Tracks all user actions, system events, and security incidents.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class SecurityAuditLog(models.Model):
    """
    Comprehensive audit logging for all system activities.
    Tracks user actions, system events, and security incidents.
    """
    
    ACTION_CHOICES = (
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('register', 'User Registration'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        ('role_change', 'Role Change'),
        ('verification_request', 'Verification Request'),
        ('verification_approve', 'Verification Approved'),
        ('verification_reject', 'Verification Rejected'),
        ('case_create', 'Case Created'),
        ('case_update', 'Case Updated'),
        ('case_delete', 'Case Deleted'),
        ('case_verify', 'Case Verified'),
        ('case_close', 'Case Closed'),
        ('match_create', 'Match Created'),
        ('match_confirm', 'Match Confirmed'),
        ('match_reject', 'Match Rejected'),
        ('contact_request', 'Contact Request'),
        ('sighting_report', 'Sighting Reported'),
        ('admin_action', 'Admin Action'),
        ('security_event', 'Security Event'),
        ('api_access', 'API Access'),
        ('file_upload', 'File Upload'),
        ('export_data', 'Data Export'),
        ('system_error', 'System Error'),
    )
    
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    # Core fields
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='User who performed the action (null for system events)'
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text='Type of action performed'
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='low',
        help_text='Severity level of the event'
    )
    
    # Details
    details = models.TextField(
        blank=True,
        help_text='Human-readable description of the event'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Structured data about the event (IP, user agent, etc.)'
    )
    
    # Object references
    content_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='Type of object affected (e.g., MissingPerson, FoundPerson)'
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID of the object affected'
    )
    
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        help_text='String representation of the affected object'
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text='When the event occurred'
    )
    
    session_key = models.CharField(
        max_length=40,
        blank=True,
        help_text='Django session key for tracking user sessions'
    )
    
    # Security fields
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address from which the action originated'
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text='Browser/user agent string'
    )
    
    success = models.BooleanField(
        default=True,
        help_text='Whether the action was successful'
    )
    
    # Additional context
    organization = models.CharField(
        max_length=200,
        blank=True,
        help_text='Organization context (if applicable)'
    )
    
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Geographic location (if available)'
    )
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        user_str = f"{self.user}" if self.user else "System"
        return f"{user_str} - {self.get_action_display()} - {self.timestamp}"
    
    @classmethod
    def log_action(cls, user=None, action='system_error', details='', 
                   severity='low', metadata=None, content_type=None, 
                   object_id=None, object_repr=None, ip_address=None, 
                   user_agent=None, success=True, request=None):
        """
        Convenience method to create audit log entries.
        """
        if request and not ip_address:
            ip_address = cls.get_client_ip(request)
        if request and not user_agent:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        if request and hasattr(request, 'session'):
            session_key = request.session.session_key
        else:
            session_key = None
        
        return cls.objects.create(
            user=user,
            action=action,
            severity=severity,
            details=details,
            metadata=metadata or {},
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            session_key=session_key
        )
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityIncident(models.Model):
    """
    Track security incidents and violations.
    """
    
    INCIDENT_TYPES = (
        ('brute_force', 'Brute Force Attack'),
        ('suspicious_login', 'Suspicious Login Activity'),
        ('privilege_escalation', 'Privilege Escalation Attempt'),
        ('data_breach', 'Potential Data Breach'),
        ('unauthorized_access', 'Unauthorized Access Attempt'),
        ('malicious_request', 'Malicious Request Pattern'),
        ('account_takeover', 'Account Takeover Attempt'),
        ('session_hijack', 'Session Hijacking Attempt'),
        ('dos_attack', 'Denial of Service'),
        ('vulnerability_scan', 'Vulnerability Scanning'),
    )
    
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    )
    
    # Incident details
    incident_type = models.CharField(
        max_length=50,
        choices=INCIDENT_TYPES,
        help_text='Type of security incident'
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        help_text='Severity level of the incident'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        help_text='Current status of the incident'
    )
    
    description = models.TextField(
        help_text='Detailed description of the incident'
    )
    
    # Affected entities
    affected_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='security_incidents',
        help_text='Users affected by this incident'
    )
    
    ip_addresses = models.JSONField(
        default=list,
        blank=True,
        help_text='List of IP addresses involved in the incident'
    )
    
    # Investigation details
    investigation_notes = models.TextField(
        blank=True,
        help_text='Notes from security investigation'
    )
    
    resolution_details = models.TextField(
        blank=True,
        help_text='How the incident was resolved'
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional structured data about the incident'
    )
    
    # Timestamps
    detected_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the incident was detected'
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the incident was resolved'
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents',
        help_text='Admin assigned to investigate this incident'
    )
    
    class Meta:
        verbose_name = 'Security Incident'
        verbose_name_plural = 'Security Incidents'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['incident_type', 'detected_at']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['detected_at']),
        ]
    
    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.get_severity_display()} - {self.detected_at}"
    
    def resolve(self, resolution_details='', resolved_by=None):
        """Mark incident as resolved."""
        self.status = 'resolved'
        self.resolution_details = resolution_details
        self.resolved_at = timezone.now()
        if resolved_by:
            self.assigned_to = resolved_by
        self.save()
        
        # Log the resolution
        SecurityAuditLog.log_action(
            user=resolved_by,
            action='security_event',
            details=f'Security incident resolved: {self.incident_type}',
            severity='medium',
            metadata={'incident_id': self.id, 'resolution': resolution_details}
        )


class SystemLog(models.Model):
    """
    System-level logging for errors, performance, and maintenance.
    """
    
    LOG_LEVELS = (
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    )
    
    CATEGORIES = (
        ('authentication', 'Authentication'),
        ('authorization', 'Authorization'),
        ('database', 'Database'),
        ('api', 'API'),
        ('file_system', 'File System'),
        ('email', 'Email System'),
        ('backup', 'Backup System'),
        ('performance', 'Performance'),
        ('security', 'Security'),
        ('maintenance', 'Maintenance'),
    )
    
    level = models.CharField(
        max_length=20,
        choices=LOG_LEVELS,
        help_text='Log level'
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORIES,
        help_text='Log category'
    )
    
    message = models.TextField(
        help_text='Log message'
    )
    
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional structured data'
    )
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text='When the log entry was created'
    )
    
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text='Source of the log entry (module, function, etc.)'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs',
        help_text='User associated with this log entry (if applicable)'
    )
    
    class Meta:
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_level_display()} - {self.category} - {self.message[:50]}"
    
    @classmethod
    def log(cls, level, category, message, details=None, source=None, user=None):
        """Convenience method to create system log entries."""
        return cls.objects.create(
            level=level,
            category=category,
            message=message,
            details=details or {},
            source=source,
            user=user
        )


class DataExport(models.Model):
    """
    Track data exports for compliance and audit purposes.
    """
    
    EXPORT_TYPES = (
        ('user_data', 'User Data Export'),
        ('case_data', 'Case Data Export'),
        ('audit_logs', 'Audit Log Export'),
        ('analytics', 'Analytics Export'),
        ('backup', 'System Backup'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='data_exports',
        help_text='User who requested the export'
    )
    
    export_type = models.CharField(
        max_length=20,
        choices=EXPORT_TYPES,
        help_text='Type of data exported'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current status of the export'
    )
    
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Path to the exported file'
    )
    
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text='Size of the exported file in bytes'
    )
    
    record_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Number of records exported'
    )
    
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text='Filters applied to the export'
    )
    
    # Timestamps
    requested_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the export was requested'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the export was completed'
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the export file expires'
    )
    
    # Security
    download_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of times the file has been downloaded'
    )
    
    last_downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the file was last downloaded'
    )
    
    class Meta:
        verbose_name = 'Data Export'
        verbose_name_plural = 'Data Exports'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['user', 'requested_at']),
            models.Index(fields=['status', 'requested_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_export_type_display()} - {self.status}"
    
    def mark_completed(self, file_path, file_size=None, record_count=None):
        """Mark export as completed."""
        self.status = 'completed'
        self.file_path = file_path
        self.file_size = file_size
        self.record_count = record_count
        self.completed_at = timezone.now()
        self.expires_at = timezone.now() + timezone.timedelta(days=7)  # 7 days expiry
        self.save()
        
        # Log the completion
        SecurityAuditLog.log_action(
            user=self.user,
            action='export_data',
            details=f'Data export completed: {self.export_type}',
            metadata={
                'export_id': self.id,
                'file_size': file_size,
                'record_count': record_count
            }
        )
    
    def increment_download(self):
        """Increment download count and update timestamp."""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save()
        
        # Log the download
        SecurityAuditLog.log_action(
            user=self.user,
            action='export_data',
            details=f'Data export downloaded: {self.export_type}',
            metadata={'export_id': self.id, 'download_count': self.download_count}
        )
