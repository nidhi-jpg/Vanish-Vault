"""
Notification Integration Examples for VanishVault
Shows how to integrate the notification service in existing views
"""

# Example 1: Integration in create_missing_person view
def create_missing_person_with_notifications(request):
    """
    Example: How to integrate notifications in create_missing_person view
    """
    if request.method == 'POST':
        # ... existing form processing logic ...
        
        # After creating the missing person:
        missing_person = MissingPerson.objects.create(
            # ... existing fields ...
        )
        
        # INTEGRATION: Send notifications for case submission
        from .services.notification_service import NotificationService
        NotificationService.notify_case_submitted(missing_person)
        
        messages.success(request, 'Case submitted successfully! Police will review your case.')
        return redirect('core:missing_detail', pk=missing_person.pk)


# Example 2: Integration in verify_missing_person view
def verify_missing_person_with_notifications(request, person_id):
    """
    Example: How to integrate notifications in case verification
    """
    missing_person = get_object_or_404(MissingPerson, pk=person_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify':
            # ... existing verification logic ...
            missing_person.status = 'verified'
            missing_person.verified_by = request.user
            missing_person.verified_at = timezone.now()
            missing_person.save()
            
            # INTEGRATION: Send notifications for case verification
            from .services.notification_service import NotificationService
            NotificationService.notify_case_verified(missing_person, request.user)
            
            messages.success(request, 'Case verified successfully!')
            
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '')
            
            # ... existing rejection logic ...
            missing_person.status = 'rejected'
            missing_person.rejection_reason = rejection_reason
            missing_person.save()
            
            # INTEGRATION: Send notifications for case rejection
            from .services.notification_service import NotificationService
            NotificationService.notify_case_rejected(
                missing_person, 
                request.user, 
                rejection_reason
            )
            
            messages.success(request, 'Case rejected with reason provided.')
        
        return redirect('core:dashboard')


# Example 3: Integration in report_sighting view
def report_sighting_with_notifications(request, person_id):
    """
    Example: How to integrate notifications in sighting report
    """
    person = get_object_or_404(MissingPerson, pk=person_id)
    
    if request.method == 'POST':
        # ... existing sighting creation logic ...
        sighting = Sighting.objects.create(
            # ... existing fields ...
        )
        
        # INTEGRATION: Send notifications for sighting report
        from .services.notification_service import NotificationService
        NotificationService.notify_sighting_reported(sighting)
        
        messages.success(request, 'Sighting reported successfully!')
        return redirect('core:missing_detail', pk=person_id)


# Example 4: Integration in face_search view
def face_search_with_notifications(request):
    """
    Example: How to integrate notifications in face search
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('image')
        missing_person_id = request.POST.get('missing_person_id')
        
        missing_person = get_object_or_404(MissingPerson, pk=missing_person_id)
        
        # ... existing face search logic ...
        match_score = 0.92  # Example match score
        matched_person = missing_person  # Example match
        
        # INTEGRATION: Log face search and send notifications
        from .services.notification_service import NotificationService
        search_log = NotificationService.log_face_search(
            performed_by=request.user if request.user.is_authenticated else None,
            missing_person=missing_person,
            uploaded_image=uploaded_file,
            match_score=match_score,
            matched_person=matched_person,
            search_results={'confidence': match_score, 'matches': [...]},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'match_score': match_score,
            'search_log_id': search_log.id
        })


# Example 5: Integration in assign_case view
def assign_case_with_notifications(request, person_id):
    """
    Example: How to integrate notifications when assigning cases
    """
    missing_person = get_object_or_404(MissingPerson, pk=person_id)
    
    if request.method == 'POST':
        officer_id = request.POST.get('officer_id')
        officer = get_object_or_404(User, pk=officer_id, role=User.Roles.POLICE)
        
        # ... existing assignment logic ...
        missing_person.assigned_officer = officer
        missing_person.assigned_at = timezone.now()
        missing_person.save()
        
        # INTEGRATION: Send notifications for police assignment
        from .services.notification_service import NotificationService
        NotificationService.notify_police_assigned(
            missing_person, 
            officer, 
            request.user
        )
        
        messages.success(request, f'Case assigned to {officer.get_full_name() or officer.username}')
        return redirect('core:missing_detail', pk=person_id)


# Example 6: Integration in update_case_status view
def update_case_status_with_notifications(request, person_id):
    """
    Example: How to integrate notifications when updating case status
    """
    missing_person = get_object_or_404(MissingPerson, pk=person_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        old_status = missing_person.status
        
        # ... existing status update logic ...
        missing_person.status = new_status
        missing_person.save()
        
        # INTEGRATION: Send notifications for status update
        from .services.notification_service import NotificationService
        NotificationService.notify_case_status_updated(
            missing_person,
            old_status,
            new_status,
            request.user
        )
        
        messages.success(request, f'Case status updated to {new_status.title()}')
        return redirect('core:missing_detail', pk=person_id)


# Example 7: Dashboard integration for admin activity feed
def admin_dashboard_with_notifications(request):
    """
    Example: How to integrate notifications in admin dashboard
    """
    # ... existing dashboard logic ...
    
    # INTEGRATION: Get recent notifications for activity feed
    from .services.notification_service import NotificationService
    from .notification_models import Notification, FaceSearchLog
    
    # Get recent activity
    recent_notifications = Notification.objects.select_related(
        'sender', 'recipient', 'missing_person', 'sighting'
    ).order_by('-created_at')[:20]
    
    # Get recent face searches
    recent_face_searches = FaceSearchLog.objects.select_related(
        'performed_by', 'missing_person', 'matched_person'
    ).order_by('-created_at')[:10]
    
    # Get high confidence matches
    high_confidence_matches = FaceSearchLog.objects.filter(
        match_score__gte=0.85
    ).select_related('performed_by', 'missing_person').order_by('-created_at')[:5]
    
    context.update({
        'recent_notifications': recent_notifications,
        'recent_face_searches': recent_face_searches,
        'high_confidence_matches': high_confidence_matches,
    })
    
    return render(request, 'core/dashboard.html', context)


# Helper function to get client IP
def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Example 8: Notification center for users
def notification_center(request):
    """
    Example: Notification center page for users
    """
    from .services.notification_service import NotificationService
    
    # Get user's notifications
    notifications = NotificationService.get_recent_notifications(
        request.user, 
        limit=20
    )
    
    # Get unread count
    unread_count = NotificationService.get_unread_count(request.user)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'core/notification_center.html', context)


# Example 9: Mark notifications as read
def mark_notification_read(request, notification_id):
    """
    Example: Mark a notification as read
    """
    notification = get_object_or_404(
        Notification, 
        pk=notification_id, 
        recipient=request.user
    )
    
    from .services.notification_service import NotificationService
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/'))


# Example 10: Mark all notifications as read
def mark_all_notifications_read(request):
    """
    Example: Mark all notifications as read for a user
    """
    from .services.notification_service import NotificationService
    count = NotificationService.mark_all_as_read(request.user)
    
    messages.success(request, f'Marked {count} notifications as read.')
    return redirect('core:notification_center')
