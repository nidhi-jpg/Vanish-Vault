"""
Centralized Notification Service for VanishVault
Handles all notification creation, delivery, and management
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from typing import List, Dict, Optional, Any
import logging

from ..models import (
    MissingPerson, Sighting, User, Notification, 
    NotificationTemplate, NotificationPreference, FaceSearchLog
)

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Centralized service for managing all notifications in the system
    """
    
    @staticmethod
    def create_notification(
        recipient: User,
        title: str,
        message: str,
        notification_type: str,
        priority: str = Notification.NotificationPriority.MEDIUM,
        sender: Optional[User] = None,
        missing_person: Optional[MissingPerson] = None,
        sighting: Optional[Sighting] = None,
        send_email: bool = True
    ) -> Notification:
        """
        Create a single notification
        
        Args:
            recipient: User to receive notification
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            sender: User who sent notification (optional)
            missing_person: Related missing person (optional)
            sighting: Related sighting (optional)
            data: Additional data (optional)
            send_email: Whether to send email notification
        
        Returns:
            Created notification object
        """
        # Check user preferences
        try:
            preferences = recipient.notification_preferences
            should_show_app = preferences.should_show_app(notification_type)
            should_send_email = send_email and preferences.should_send_email(notification_type)
        except NotificationPreference.DoesNotExist:
            # Create default preferences if they don't exist
            preferences = NotificationPreference.objects.create(user=recipient)
            should_show_app = True
            should_send_email = send_email
        
        # Create notification
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            missing_person=missing_person,
            sighting=sighting
        )
        
        # Send email if enabled
        if should_send_email and recipient.email:
            NotificationService._send_email_notification(notification)
        
        logger.info(f"Created {notification_type} notification for {recipient.username}")
        return notification
    
    @staticmethod
    def notify_case_submitted(missing_person: MissingPerson) -> List[Notification]:
        """
        Send notifications when a new case is submitted
        
        Recipients:
        - Police users: "New case pending verification"
        - Admin users: "New case submitted"
        - Citizen who submitted: "Your case is under verification"
        """
        notifications = []
        
        # Get police and admin users
        police_users = User.objects.filter(role=User.Roles.POLICE, is_active=True)
        admin_users = User.objects.filter(role=User.Roles.ADMIN, is_active=True)
        
        # Notify police officers
        for police in police_users:
            notification = NotificationService.create_notification(
                recipient=police,
                title="New Case Pending Verification",
                message=f"A new missing person case has been submitted: {missing_person.full_name}. "
                        f"Please review and verify the case details.",
                notification_type=Notification.NotificationType.CASE_SUBMITTED,
                priority=Notification.NotificationPriority.HIGH,
                missing_person=missing_person,
                data={'case_id': missing_person.id, 'submitted_by': missing_person.reported_by.username}
            )
            notifications.append(notification)
        
        # Notify admin users
        for admin in admin_users:
            notification = NotificationService.create_notification(
                recipient=admin,
                title="New Case Submitted",
                message=f"New missing person case submitted: {missing_person.full_name} "
                        f"by {missing_person.reported_by.username}. Case is pending police verification.",
                notification_type=NotificationType.CASE_SUBMITTED,
                priority=NotificationPriority.MEDIUM,
                missing_person=missing_person,
                data={'case_id': missing_person.id, 'submitted_by': missing_person.reported_by.username}
            )
            notifications.append(notification)
        
        # Notify the citizen who submitted the case
        notification = NotificationService.create_notification(
            recipient=missing_person.reported_by,
            title="Your Case is Under Verification",
            message=f"Your missing person report for {missing_person.full_name} has been submitted "
                    f"and is currently under verification by our police team. "
                    f"You will be notified once the verification is complete.",
            notification_type=NotificationType.CASE_SUBMITTED,
            priority=NotificationPriority.MEDIUM,
            missing_person=missing_person,
            data={'case_id': missing_person.id}
        )
        notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notify_case_verified(missing_person: MissingPerson, verified_by: User) -> List[Notification]:
        """
        Send notifications when a case is verified by police
        
        Recipients:
        - Citizen who submitted: "Your case has been verified"
        - Admin users: "Case verified by Officer X"
        """
        notifications = []
        
        # Notify the citizen who submitted the case
        notification = NotificationService.create_notification(
            recipient=missing_person.reported_by,
            title="Your Case Has Been Verified",
            message=f"Great news! Your missing person case for {missing_person.full_name} "
                    f"has been verified by Officer {verified_by.get_full_name() or verified_by.username}. "
                    f"The case is now active and our team will begin investigation.",
            notification_type=NotificationType.CASE_VERIFIED,
            priority=NotificationPriority.HIGH,
            sender=verified_by,
            missing_person=missing_person,
            data={'case_id': missing_person.id, 'verified_by': verified_by.username}
        )
        notifications.append(notification)
        
        # Notify admin users
        admin_users = User.objects.filter(role=User.Roles.ADMIN, is_active=True)
        for admin in admin_users:
            notification = NotificationService.create_notification(
                recipient=admin,
                title="Case Verified",
                message=f"Case for {missing_person.full_name} has been verified by "
                        f"Officer {verified_by.get_full_name() or verified_by.username}.",
                notification_type=NotificationType.CASE_VERIFIED,
                priority=NotificationPriority.MEDIUM,
                sender=verified_by,
                missing_person=missing_person,
                data={'case_id': missing_person.id, 'verified_by': verified_by.username}
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notify_case_rejected(missing_person: MissingPerson, rejected_by: User, rejection_reason: str) -> List[Notification]:
        """
        Send notifications when a case is rejected
        
        Recipients:
        - Citizen who submitted: Rejection with reason
        - Admin users: Rejection log
        """
        notifications = []
        
        # Notify the citizen who submitted the case
        notification = NotificationService.create_notification(
            recipient=missing_person.reported_by,
            title="Case Update: Review Required",
            message=f"Your missing person case for {missing_person.full_name} requires some updates. "
                    f"Reason: {rejection_reason}. Please update the information and resubmit.",
            notification_type=NotificationType.CASE_REJECTED,
            priority=NotificationPriority.HIGH,
            sender=rejected_by,
            missing_person=missing_person,
            data={'case_id': missing_person.id, 'rejection_reason': rejection_reason}
        )
        notifications.append(notification)
        
        # Notify admin users
        admin_users = User.objects.filter(role=User.Roles.ADMIN, is_active=True)
        for admin in admin_users:
            notification = NotificationService.create_notification(
                recipient=admin,
                title="Case Rejected",
                message=f"Case for {missing_person.full_name} was rejected by "
                        f"{rejected_by.get_full_name() or rejected_by.username}. "
                        f"Reason: {rejection_reason}",
                notification_type=NotificationType.CASE_REJECTED,
                priority=NotificationPriority.MEDIUM,
                sender=rejected_by,
                missing_person=missing_person,
                data={'case_id': missing_person.id, 'rejected_by': rejected_by.username, 'rejection_reason': rejection_reason}
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notify_case_status_updated(missing_person: MissingPerson, old_status: str, new_status: str, updated_by: User) -> List[Notification]:
        """
        Send notifications when case status is updated
        
        Recipients:
        - Citizen who submitted: Status update
        - Admin users: Activity log
        - Assigned police (if any): Status update
        """
        notifications = []
        
        # Notify the citizen who submitted the case
        notification = NotificationService.create_notification(
            recipient=missing_person.reported_by,
            title=f"Case Status Updated: {new_status.title()}",
            message=f"Your missing person case for {missing_person.full_name} status has been updated "
                    f"from {old_status.title()} to {new_status.title()}. "
                    f"Updated by: {updated_by.get_full_name() or updated_by.username}",
            notification_type=NotificationType.CASE_UPDATED,
            priority=NotificationPriority.MEDIUM,
            sender=updated_by,
            missing_person=missing_person,
            data={'case_id': missing_person.id, 'old_status': old_status, 'new_status': new_status}
        )
        notifications.append(notification)
        
        # Notify admin users
        admin_users = User.objects.filter(role=User.Roles.ADMIN, is_active=True)
        for admin in admin_users:
            notification = NotificationService.create_notification(
                recipient=admin,
                title="Case Status Updated",
                message=f"Case {missing_person.id} ({missing_person.full_name}) status updated "
                        f"from {old_status.title()} to {new_status.title()} by {updated_by.username}",
                notification_type=NotificationType.CASE_UPDATED,
                priority=NotificationPriority.LOW,
                sender=updated_by,
                missing_person=missing_person,
                data={'case_id': missing_person.id, 'old_status': old_status, 'new_status': new_status}
            )
            notifications.append(notification)
        
        # Notify assigned police officer
        if missing_person.assigned_officer:
            notification = NotificationService.create_notification(
                recipient=missing_person.assigned_officer,
                title=f"Case Status Updated: {new_status.title()}",
                message=f"Assigned case {missing_person.id} ({missing_person.full_name}) status updated "
                        f"to {new_status.title()}",
                notification_type=NotificationType.CASE_UPDATED,
                priority=NotificationPriority.MEDIUM,
                sender=updated_by,
                missing_person=missing_person,
                data={'case_id': missing_person.id, 'old_status': old_status, 'new_status': new_status}
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notify_sighting_reported(sighting: Sighting) -> List[Notification]:
        """
        Send notifications when a sighting is reported
        
        Recipients:
        - Assigned police officer: New sighting
        - Admin users: Sighting logged
        - Missing person's reporter: New sighting
        """
        notifications = []
        
        # Notify assigned police officer
        if sighting.missing_person.assigned_officer:
            notification = NotificationService.create_notification(
                recipient=sighting.missing_person.assigned_officer,
                title="New Sighting Reported",
                message=f"A new sighting has been reported for {sighting.missing_person.full_name}. "
                        f"Location: {sighting.location}. Date: {sighting.date}. "
                        f"Reporter: {sighting.reporter_name or 'Anonymous'}",
                notification_type=NotificationType.SIGHTING_REPORTED,
                priority=NotificationPriority.HIGH,
                sighting=sighting,
                missing_person=sighting.missing_person,
                data={'sighting_id': sighting.id, 'location': sighting.location}
            )
            notifications.append(notification)
        
        # Notify admin users
        admin_users = User.objects.filter(role=User.Roles.ADMIN, is_active=True)
        for admin in admin_users:
            notification = NotificationService.create_notification(
                recipient=admin,
                title="New Sighting Reported",
                message=f"New sighting reported for {sighting.missing_person.full_name} "
                        f"at {sighting.location} on {sighting.date}",
                notification_type=NotificationType.SIGHTING_REPORTED,
                priority=NotificationPriority.MEDIUM,
                sighting=sighting,
                missing_person=sighting.missing_person,
                data={'sighting_id': sighting.id, 'location': sighting.location}
            )
            notifications.append(notification)
        
        # Notify the missing person's reporter
        notification = NotificationService.create_notification(
            recipient=sighting.missing_person.reported_by,
            title="New Sighting Reported",
            message=f"A new sighting has been reported for {sighting.missing_person.full_name}. "
                    f"Location: {sighting.location}. Our team will review this information.",
            notification_type=NotificationType.SIGHTING_REPORTED,
            priority=NotificationPriority.HIGH,
            sighting=sighting,
            missing_person=sighting.missing_person,
            data={'sighting_id': sighting.id, 'location': sighting.location}
        )
        notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def log_face_search(
        performed_by: User,
        missing_person: MissingPerson,
        uploaded_image,
        match_score: Optional[float] = None,
        matched_person: Optional[MissingPerson] = None,
        search_results: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> FaceSearchLog:
        """
        Log a face search operation and send notifications for high confidence matches
        
        Args:
            performed_by: User who performed the search
            missing_person: Person being searched for
            uploaded_image: Image used for search
            match_score: Best match score
            matched_person: Person that was matched
            search_results: Complete search results
            ip_address: IP address
            user_agent: Browser user agent
        
        Returns:
            Created FaceSearchLog object
        """
        # Log the search
        search_log = FaceSearchLog.objects.create(
            performed_by=performed_by,
            missing_person=missing_person,
            uploaded_image=uploaded_image,
            match_score=match_score,
            matched_person=matched_person,
            search_results=search_results or {},
            ip_address=ip_address,
            user_agent=user_agent or ''
        )
        
        # Send notifications based on match score
        if match_score and match_score >= 0.70:
            notifications = []
            
            # Determine priority based on score
            priority = NotificationPriority.URGENT if match_score >= 0.85 else NotificationPriority.HIGH
            
            # Get police and admin users
            police_users = User.objects.filter(role=User.Roles.POLICE, is_active=True)
            admin_users = User.objects.filter(role=User.Roles.ADMIN, is_active=True)
            
            # Create notification message
            confidence_pct = f"{match_score * 100:.1f}%"
            match_type = "High Confidence" if match_score >= 0.85 else "Medium Confidence"
            
            message = (f"{match_type} face match found! "
                      f"Search for {missing_person.full_name} returned {confidence_pct} match "
                      f"performed by {performed_by.get_full_name() or performed_by.username}")
            
            # Notify police
            for police in police_users:
                notification = NotificationService.create_notification(
                    recipient=police,
                    title=f"{match_type} Face Match Found",
                    message=message,
                    notification_type=NotificationType.HIGH_CONFIDENCE_MATCH if match_score >= 0.85 else NotificationType.FACE_SEARCH_PERFORMED,
                    priority=priority,
                    sender=performed_by,
                    missing_person=missing_person,
                    data={
                        'search_log_id': search_log.id,
                        'match_score': match_score,
                        'confidence_percentage': confidence_pct,
                        'searched_by': performed_by.username
                    }
                )
                notifications.append(notification)
            
            # Notify admin
            for admin in admin_users:
                notification = NotificationService.create_notification(
                    recipient=admin,
                    title=f"{match_type} Face Match Found",
                    message=message,
                    notification_type=NotificationType.HIGH_CONFIDENCE_MATCH if match_score >= 0.85 else NotificationType.FACE_SEARCH_PERFORMED,
                    priority=priority,
                    sender=performed_by,
                    missing_person=missing_person,
                    data={
                        'search_log_id': search_log.id,
                        'match_score': match_score,
                        'confidence_percentage': confidence_pct,
                        'searched_by': performed_by.username
                    }
                )
                notifications.append(notification)
            
            # Notify the missing person's reporter if it's a high confidence match
            if match_score >= 0.85:
                notification = NotificationService.create_notification(
                    recipient=missing_person.reported_by,
                    title="Potential Match Found",
                    message=f"Our AI face recognition system has found a potential match for {missing_person.full_name}. "
                            f"Our team will review this information and contact you soon.",
                    notification_type=NotificationType.HIGH_CONFIDENCE_MATCH,
                    priority=NotificationPriority.HIGH,
                    missing_person=missing_person,
                    data={
                        'search_log_id': search_log.id,
                        'match_score': match_score,
                        'confidence_percentage': confidence_pct
                    }
                )
                notifications.append(notification)
        
        logger.info(f"Face search logged by {performed_by.username} for {missing_person.full_name} - Score: {match_score or 0:.2%}")
        return search_log
    
    @staticmethod
    def notify_police_assigned(missing_person: MissingPerson, assigned_to: User, assigned_by: User) -> List[Notification]:
        """
        Send notifications when a police officer is assigned to a case
        
        Recipients:
        - Assigned police officer: Case assignment
        - Admin users: Assignment log
        """
        notifications = []
        
        # Notify the assigned police officer
        notification = NotificationService.create_notification(
            recipient=assigned_to,
            title="New Case Assigned",
            message=f"You have been assigned to case {missing_person.id}: {missing_person.full_name}. "
                    f"Please review the case details and begin investigation.",
            notification_type=NotificationType.POLICE_ASSIGNED,
            priority=NotificationPriority.HIGH,
            sender=assigned_by,
            missing_person=missing_person,
            data={'case_id': missing_person.id, 'assigned_by': assigned_by.username}
        )
        notifications.append(notification)
        
        # Notify admin users
        admin_users = User.objects.filter(role=User.Roles.ADMIN, is_active=True)
        for admin in admin_users:
            notification = NotificationService.create_notification(
                recipient=admin,
                title="Police Officer Assigned",
                message=f"Officer {assigned_to.get_full_name() or assigned_to.username} has been assigned "
                        f"to case {missing_person.id}: {missing_person.full_name}",
                notification_type=NotificationType.POLICE_ASSIGNED,
                priority=NotificationPriority.MEDIUM,
                sender=assigned_by,
                missing_person=missing_person,
                data={'case_id': missing_person.id, 'assigned_to': assigned_to.username}
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def _send_email_notification(notification: Notification):
        """
        Send email notification for a given notification
        
        Args:
            notification: Notification object to send email for
        """
        try:
            # Get email template
            try:
                template = NotificationTemplate.objects.get(
                    notification_type=notification.notification_type,
                    is_active=True
                )
                subject = template.subject_template
                body = template.body_template
            except NotificationTemplate.DoesNotExist:
                # Fallback templates
                subject = f"VanishVault: {notification.title}"
                body = f"""
Hello {notification.recipient.first_name or notification.recipient.username},

{notification.message}

View details: {settings.SITE_URL}{notification.get_action_url()}

Thank you,
VanishVault Team
"""
            
            # Render template with context
            context = {
                'notification': notification,
                'user': notification.recipient,
                'site_url': settings.SITE_URL,
            }
            
            # Use Django's template rendering if template exists
            if 'template' in locals():
                subject = render_to_string(subject, context).strip()
                body = render_to_string(body, context)
            
            # Send email
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                fail_silently=False
            )
            
            # Mark email as sent
            notification.is_email_sent = True
            notification.save(update_fields=['is_email_sent'])
            
            logger.info(f"Email sent to {notification.recipient.email} for notification {notification.id}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification {notification.id}: {str(e)}")
    
    @staticmethod
    def get_unread_count(user: User) -> int:
        """Get count of unread notifications for a user"""
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
    
    @staticmethod
    def get_recent_notifications(user: User, limit: int = 10) -> List[Notification]:
        """Get recent notifications for a user"""
        return Notification.objects.filter(
            recipient=user
        ).select_related(
            'sender', 'missing_person', 'sighting'
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def mark_all_as_read(user: User) -> int:
        """Mark all notifications as read for a user"""
        count = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        logger.info(f"Marked {count} notifications as read for {user.username}")
        return count
    
    @staticmethod
    def cleanup_old_notifications(days_old: int = 30):
        """Clean up old read notifications"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        
        deleted_count = Notification.objects.filter(
            is_read=True,
            read_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return deleted_count
