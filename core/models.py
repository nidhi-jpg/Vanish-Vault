from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.crypto import get_random_string
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended user model with role-based access control"""
    
    class Roles(models.TextChoices):
        CITIZEN = 'citizen', 'Citizen'
        POLICE = 'police', 'Police Officer'
        NGO = 'ngo', 'NGO Worker'
        VOLUNTEER = 'volunteer', 'Volunteer'
        ADMIN = 'admin', 'Administrator'
    
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CITIZEN,
        help_text='User role determines access level and permissions'
    )
    
    organization = models.CharField(
        max_length=200,
        blank=True,
        help_text='Organization name (for police, NGO, volunteer roles)'
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone number'
    )
    
    phone_verified = models.BooleanField(
        default=False,
        help_text='Whether phone number has been verified'
    )
    
    id_document = models.FileField(
        upload_to='id_documents/',
        blank=True,
        null=True,
        help_text='ID document for verification (police, NGO roles)'
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether user identity has been verified by admin'
    )
    verified_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_users',
        help_text='Admin user who verified this account'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when verification was completed'
    )
    verification_notes = models.TextField(
        blank=True,
        help_text='Internal notes about verification checks'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_police(self):
        return self.role in [self.Roles.POLICE, self.Roles.ADMIN]
    
    def is_ngo(self):
        return self.role in [self.Roles.NGO, self.Roles.ADMIN]
    
    def can_verify_cases(self):
        return self.role in [self.Roles.POLICE, self.Roles.ADMIN]


class MissingPerson(models.Model):
    """Model for missing person reports"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('closed', 'Case Closed'),
        ('rejected', 'Rejected'),
    )
    
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    )
    
    # Core identification
    case_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Unique case identifier'
    )
    
    full_name = models.CharField(
        max_length=200,
        help_text='Full name of missing person'
    )
    
    age = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Age at time of disappearance'
    )
    
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )
    
    # Physical description
    height = models.CharField(
        max_length=50,
        blank=True,
        help_text='Height (e.g., 5\'8", 175cm)'
    )
    
    weight = models.CharField(
        max_length=50,
        blank=True,
        help_text='Weight (e.g., 150 lbs, 68kg)'
    )
    
    hair_color = models.CharField(
        max_length=50,
        blank=True
    )
    
    eye_color = models.CharField(
        max_length=50,
        blank=True
    )
    
    distinguishing_features = models.TextField(
        blank=True,
        help_text='Scars, tattoos, birthmarks, etc.'
    )
    
    # Disappearance details
    last_seen_location = models.CharField(
        max_length=255,
        help_text='Last known location'
    )
    
    last_seen_date = models.DateField(
        null=True,
        blank=True
    )
    
    last_seen_time = models.TimeField(
        null=True,
        blank=True
    )
    
    # Case details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Additional details about disappearance'
    )
    
    # Media
    photo = models.ImageField(
        upload_to='missing_persons/',
        blank=True,
        null=True
    )
    
    additional_photos = models.ManyToManyField(
        'Photo',
        blank=True,
        related_name='missing_person_photos'
    )

    # AI face embedding data (for fast face matching)
    # NOTE: Using TextField instead of JSONField for SQLite compatibility.
    #       Store JSON-serialized list (e.g. via json.dumps / json.loads) in service layer.
    face_embedding = models.TextField(
        null=True,
        blank=True,
        help_text='AI-generated face embedding vector stored as JSON text'
    )
    face_embedding_model = models.CharField(
        max_length=50,
        blank=True,
        help_text='Name of the AI model used to generate the face embedding'
    )
    face_embedding_created_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the face embedding was last generated'
    )
    
    # Reporter details
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_missing'
    )
    
    reporter_relationship = models.CharField(
        max_length=100,
        blank=True,
        help_text='Relationship to missing person'
    )
    
    reporter_phone = models.CharField(
        max_length=20,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_cases'
    )
    
    class Meta:
        verbose_name = 'Missing Person'
        verbose_name_plural = 'Missing Persons'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.case_id}"
    
    def save(self, *args, **kwargs):
        if not self.case_id:
            # Generate unique case ID: MP-YYYY-XXXXX
            year = self.created_at.year if self.created_at else timezone.now().year
            random_part = get_random_string(5, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            self.case_id = f"MP-{year}-{random_part}"
        super().save(*args, **kwargs)
    
    @property
    def days_missing(self):
        """Calculate days since last seen"""
        if self.last_seen_date:
            from django.utils import timezone
            return (timezone.now().date() - self.last_seen_date).days
        return None


class FoundPerson(models.Model):
    """Model for unidentified found persons"""
    
    STATUS_CHOICES = (
        ('unidentified', 'Unidentified'),
        ('identified', 'Identified'),
        ('reunited', 'Reunited with Family'),
    )
    
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    )
    
    # Basic info
    case_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Unique found person case identifier'
    )
    
    possible_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Name if known or provided'
    )
    
    estimated_age = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )
    
    # Physical description
    height = models.CharField(max_length=50, blank=True)
    weight = models.CharField(max_length=50, blank=True)
    hair_color = models.CharField(max_length=50, blank=True)
    eye_color = models.CharField(max_length=50, blank=True)
    distinguishing_features = models.TextField(blank=True)
    
    # Found details
    found_location = models.CharField(max_length=255)
    found_date = models.DateField()
    found_time = models.TimeField(null=True, blank=True)
    
    # Current status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unidentified'
    )
    
    notes = models.TextField(
        blank=True,
        help_text='Additional details about found person'
    )
    
    # Media
    photo = models.ImageField(
        upload_to='found_persons/',
        blank=True,
        null=True
    )
    
    additional_photos = models.ManyToManyField(
        'Photo',
        blank=True,
        related_name='found_person_photos'
    )

    # AI face embedding data (for fast face matching)
    # NOTE: Using TextField instead of JSONField for SQLite compatibility.
    #       Store JSON-serialized list (e.g. via json.dumps / json.loads) in service layer.
    face_embedding = models.TextField(
        null=True,
        blank=True,
        help_text='AI-generated face embedding vector stored as JSON text'
    )
    face_embedding_model = models.CharField(
        max_length=50,
        blank=True,
        help_text='Name of the AI model used to generate the face embedding'
    )
    face_embedding_created_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the face embedding was last generated'
    )
    
    # Organization details
    found_by_organization = models.CharField(
        max_length=200,
        help_text='Hospital, NGO, or organization that found the person'
    )
    
    contact_person = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    identified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Found Person'
        verbose_name_plural = 'Found Persons'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.possible_name or 'Unidentified'} - {self.case_id}"
    
    def save(self, *args, **kwargs):
        if not self.case_id:
            # Generate unique case ID: FP-YYYY-XXXXX
            year = timezone.now().year
            random_part = get_random_string(5, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            self.case_id = f"FP-{year}-{random_part}"
        super().save(*args, **kwargs)


class PotentialMatch(models.Model):
    """
    AI-suggested potential matches between missing and found persons.
    These are NEVER auto-confirmed; humans must review and update status.
    """

    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('confirmed', 'Confirmed Match'),
        ('rejected', 'Rejected / Not a Match'),
    )

    # Either side may be null if you extend in future, but for now we require both
    missing_person = models.ForeignKey(
        MissingPerson,
        on_delete=models.CASCADE,
        related_name='potential_matches'
    )
    found_person = models.ForeignKey(
        FoundPerson,
        on_delete=models.CASCADE,
        related_name='potential_matches'
    )

    # Source of the match (which report triggered the check)
    triggered_by = models.CharField(
        max_length=10,
        choices=(
            ('missing', 'New Missing Report'),
            ('found', 'New Found Report'),
        ),
        help_text='Which type of report triggered this AI match suggestion'
    )

    # AI similarity metrics
    distance = models.FloatField(
        help_text='Raw distance between face embeddings (lower = more similar)'
    )
    confidence = models.FloatField(
        help_text='Derived confidence score (0-100) from the AI model'
    )
    ai_model = models.CharField(
        max_length=50,
        blank=True,
        help_text='Name of AI model used during matching (e.g. DeepFace, face_recognition)'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Human review status of this potential match'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_matches',
        help_text='Admin/Officer who reviewed this match'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this match was reviewed by a human'
    )
    notes = models.TextField(
        blank=True,
        help_text='Reviewer notes and justification'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Potential Match'
        verbose_name_plural = 'Potential Matches'
        unique_together = (
            # Prevent duplicate AI suggestions for the same pair
            ('missing_person', 'found_person', 'triggered_by'),
        )
        ordering = ['-confidence', 'distance']

    def __str__(self):
        return f"Potential match: {self.missing_person.case_id} ↔ {self.found_person.case_id} ({self.confidence:.1f}%)"


class Sighting(models.Model):
    """Model for sighting reports"""
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('investigating', 'Under Investigation'),
        ('verified', 'Verified'),
        ('false_alarm', 'False Alarm'),
    )
    
    missing_person = models.ForeignKey(
        MissingPerson,
        on_delete=models.CASCADE,
        related_name='sightings'
    )
    
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_sightings'
    )
    
    # Sighting details
    location = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    
    description = models.TextField(
        help_text='Detailed description of the sighting'
    )
    
    confidence_level = models.CharField(
        max_length=20,
        choices=[
            ('high', 'High - I\'m certain it was them'),
            ('medium', 'Medium - I think it was them'),
            ('low', 'Low - I\'m not sure'),
        ],
        default='medium'
    )
    
    # Contact details
    reporter_name = models.CharField(max_length=200, blank=True)
    reporter_phone = models.CharField(max_length=20, blank=True)
    reporter_email = models.EmailField(blank=True)
    
    # Physical description (optional)
    estimated_age = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text='Estimated age in years (1-120)'
    )
    estimated_height_cm = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        help_text='Estimated height in centimeters (50-300cm)'
    )
    
    # Photo evidence (optional)
    photo = models.ImageField(
        upload_to='sighting_photos/',
        blank=True,
        null=True,
        help_text='Photo of the person during the sighting (optional but recommended)'
    )
    
    # AI Face Matching
    ai_match_score = models.FloatField(
        null=True,
        blank=True,
        help_text='AI confidence score (0.0 to 1.0) for face match with missing person'
    )
    
    # Status and verification
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_sightings'
    )
    
    verification_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Sighting'
        verbose_name_plural = 'Sightings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sighting of {self.missing_person.full_name} at {self.location}"


class VerificationTask(models.Model):
    """Model for verification tasks assigned to police/admin"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    task_type = models.CharField(
        max_length=50,
        choices=[
            ('case_verification', 'Case Verification'),
            ('sighting_verification', 'Sighting Verification'),
            ('user_verification', 'User Verification'),
        ]
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    
    related_case = models.ForeignKey(
        MissingPerson,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='verification_tasks'
    )
    
    related_sighting = models.ForeignKey(
        Sighting,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='verification_tasks'
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    description = models.TextField()
    notes = models.TextField(blank=True)
    
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Verification Task'
        verbose_name_plural = 'Verification Tasks'
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.get_status_display()}"


class Notification(models.Model):
    """Enhanced notification model for all system notifications"""
    
    class NotificationType(models.TextChoices):
        """Types of notifications in the system"""
        CASE_SUBMITTED = 'case_submitted', 'Case Submitted'
        CASE_VERIFIED = 'case_verified', 'Case Verified'
        CASE_REJECTED = 'case_rejected', 'Case Rejected'
        CASE_UPDATED = 'case_updated', 'Case Updated'
        SIGHTING_REPORTED = 'sighting_reported', 'Sighting Reported'
        FACE_SEARCH_PERFORMED = 'face_search_performed', 'Face Search Performed'
        HIGH_CONFIDENCE_MATCH = 'high_confidence_match', 'High Confidence Match'
        POLICE_ASSIGNED = 'police_assigned', 'Police Assigned'
        SYSTEM_ALERT = 'system_alert', 'System Alert'
        # Legacy types for backward compatibility
        CASE_UPDATE = 'case_update', 'Case Update'
        NEW_SIGHTING = 'sighting_report', 'New Sighting'
        VERIFICATION_COMPLETE = 'verification_complete', 'Verification Complete'
        SYSTEM = 'system', 'System Message'

    class NotificationPriority(models.TextChoices):
        """Priority levels for notifications"""
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='User who receives this notification'
    )
    
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        help_text='User who triggered this notification (if applicable)'
    )
    
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        help_text='Type of notification'
    )
    
    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.MEDIUM,
        help_text='Priority level of this notification'
    )
    
    title = models.CharField(
        max_length=200,
        help_text='Notification title'
    )
    
    message = models.TextField(
        help_text='Detailed notification message'
    )
    
    # Related objects (optional)
    missing_person = models.ForeignKey(
        'MissingPerson',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Related missing person case (if applicable)'
    )
    
    sighting = models.ForeignKey(
        'Sighting',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Related sighting (if applicable)'
    )
    
    # Status and tracking
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the notification has been read'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the notification was created'
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the notification was read'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def is_expired(self):
        """Check if notification is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_action_url(self):
        """Get URL for the action related to this notification"""
        if self.missing_person:
            return f"/missing/{self.missing_person.id}/"
        elif self.sighting:
            return f"/sighting/{self.sighting.id}/"
        return "/dashboard/"
    
    def get_data(self):
        """Get data as dictionary"""
        import json
        try:
            return json.loads(self.data) if self.data else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_data(self, data_dict):
        """Set data from dictionary"""
        import json
        self.data = json.dumps(data_dict or {})
        self.save(update_fields=['data'])


class NotificationTemplate(models.Model):
    """Email notification templates for different notification types"""
    
    notification_type = models.CharField(
        max_length=30,
        choices=Notification.NotificationType.choices,
        unique=True,
        help_text='Notification type this template is for'
    )
    
    subject_template = models.CharField(
        max_length=200,
        help_text='Email subject template (use Django template syntax)'
    )
    
    body_template = models.TextField(
        help_text='Email body template (use Django template syntax)'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this template is active'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['notification_type']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} Template"


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email preferences
    email_case_submitted = models.BooleanField(default=True)
    email_case_verified = models.BooleanField(default=True)
    email_case_rejected = models.BooleanField(default=True)
    email_case_updated = models.BooleanField(default=True)
    email_sighting_reported = models.BooleanField(default=True)
    email_face_search = models.BooleanField(default=True)
    email_high_confidence = models.BooleanField(default=True)
    
    # In-app preferences
    app_case_submitted = models.BooleanField(default=True)
    app_case_verified = models.BooleanField(default=True)
    app_case_rejected = models.BooleanField(default=True)
    app_case_updated = models.BooleanField(default=True)
    app_sighting_reported = models.BooleanField(default=True)
    app_face_search = models.BooleanField(default=True)
    app_high_confidence = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user']
    
    def __str__(self):
        return f"{self.user.username} Preferences"
    
    def should_send_email(self, notification_type):
        """Check if user should receive email for this notification type"""
        field_name = f"email_{notification_type}"
        return getattr(self, field_name, True)
    
    def should_show_app(self, notification_type):
        """Check if user should see in-app notification for this type"""
        field_name = f"app_{notification_type}"
        return getattr(self, field_name, True)


class FaceSearchLog(models.Model):
    """Log of all face search operations for audit and notifications"""
    
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='face_searches',
        help_text='User who performed the face search'
    )
    
    missing_person = models.ForeignKey(
        'MissingPerson',
        on_delete=models.CASCADE,
        related_name='face_searches',
        help_text='Missing person being searched for'
    )
    
    uploaded_image = models.ImageField(
        upload_to='face_searches/',
        help_text='Image used for face search'
    )
    
    match_score = models.FloatField(
        null=True,
        blank=True,
        help_text='Best match score (0.0 to 1.0)'
    )
    
    matched_person = models.ForeignKey(
        'MissingPerson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='face_search_matches',
        help_text='Person that was matched (if any)'
    )
    
    search_results = models.TextField(
        default='{}',
        blank=True,
        help_text='Complete search results data (JSON format)'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the searcher'
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text='Browser user agent'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['performed_by']),
            models.Index(fields=['missing_person']),
            models.Index(fields=['match_score']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        user = self.performed_by.username if self.performed_by else 'Anonymous'
        return f"Face Search by {user} - Score: {self.match_score or 0:.2%}"
    
    def get_confidence_percentage(self):
        """Get match score as percentage"""
        if self.match_score:
            return f"{self.match_score * 100:.1f}%"
        return "N/A"
    
    def is_high_confidence(self):
        """Check if this is a high confidence match (>85%)"""
        return self.match_score and self.match_score >= 0.85
    
    def is_medium_confidence(self):
        """Check if this is a medium confidence match (>70%)"""
        return self.match_score and self.match_score >= 0.70
    
    def get_search_results(self):
        """Get search results as dictionary"""
        import json
        try:
            return json.loads(self.search_results) if self.search_results else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_search_results(self, results_dict):
        """Set search results from dictionary"""
        import json
        self.search_results = json.dumps(results_dict or {})
        self.save(update_fields=['search_results'])


class AuditLog(models.Model):
    """Model for system audit logging"""
    
    ACTION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('verify', 'Verify'),
        ('reject', 'Reject'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} on {self.model_name} by {self.user or 'System'}"


class Photo(models.Model):
    """Model for additional photos"""
    
    image = models.ImageField(upload_to='photos/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Photo'
        verbose_name_plural = 'Photos'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.caption or f"Photo uploaded by {self.uploaded_by or 'Anonymous'}"
