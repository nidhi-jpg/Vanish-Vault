from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import MissingPerson, FoundPerson, User, PotentialMatch, AuditLog
from . import matching_service
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ReportMissingForm, ReportFoundForm


def home(request):
    """Home page view showing recent cases and search"""
    latest_missing = MissingPerson.objects.filter(status='verified').order_by('-created_at')[:6]
    latest_found = FoundPerson.objects.filter(status='unidentified').order_by('-created_at')[:6]
    
    context = {
        'latest_missing': latest_missing,
        'latest_found': latest_found,
        'total_missing': MissingPerson.objects.filter(status='verified').count(),
        'total_found': FoundPerson.objects.filter(status='unidentified').count(),
    }
    return render(request, 'core/home.html', context)


def roadmap(request):
    """User roadmap page showing how to use the platform"""
    return render(request, 'core/roadmap.html')


def search(request):
    """Search missing persons with filters"""
    from django.core.paginator import Paginator
    
    query = request.GET.get('q', '')
    gender = request.GET.get('gender', '')
    location = request.GET.get('location', '')
    age_min = request.GET.get('age_min', '')
    age_max = request.GET.get('age_max', '')
    
    # Start with active missing cases (include pending + verified so
    # people can still find reports when trying to mark someone as found).
    results = MissingPerson.objects.filter(status__in=['pending', 'verified'])
    
    if query:
        results = results.filter(full_name__icontains=query)
    if gender:
        results = results.filter(gender=gender)
    if location:
        results = results.filter(last_seen_location__icontains=location)
    if age_min:
        results = results.filter(age__gte=age_min)
    if age_max:
        results = results.filter(age__lte=age_max)
    
    # Add pagination
    paginator = Paginator(results.order_by('-created_at'), 12)  # 12 results per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'results': page_obj,
        'query': query,
        'gender_val': gender,
        'location_val': location,
        'age_min_val': age_min,
        'age_max_val': age_max,
        'page_obj': page_obj,
    }
    return render(request, 'core/search.html', context)


def found_list(request):
    """List of unidentified found persons"""
    items = FoundPerson.objects.filter(status='unidentified').order_by('-created_at')
    gender = request.GET.get('gender')
    
    if gender:
        items = items.filter(gender=gender)
    
    context = {'items': items}
    return render(request, 'core/found_list.html', context)


def missing_detail(request, pk):
    """Detailed view of a missing person case"""
    person = get_object_or_404(MissingPerson, pk=pk)
    
    # Only show full details if case is verified
    if person.status != 'verified':
        messages.warning(request, 'This case is pending verification.')
    
    context = {'person': person}
    return render(request, 'core/missing_detail.html', context)


def found_detail(request, pk):
    """Detailed view of a found person case"""
    person = get_object_or_404(FoundPerson, pk=pk)
    context = {'person': person}
    return render(request, 'core/found_detail.html', context)


@login_required(login_url='core:login')
def dashboard(request):
    """
    Admin dashboard for system oversight and verification workflow.
    
    Access rules:
    - User must be authenticated (handled by decorator)
    - User must be staff OR have role=ADMIN
    - User must be is_verified=True
    
    The dashboard does NOT show public-facing content; it only exposes:
    - Verification panels (users, cases, matches)
    - AI monitoring
    - System statistics
    - Recent audit activity
    """
    user = request.user

    # Restrict strictly to admin-type users
    if not (user.is_staff or user.role == User.Roles.ADMIN):
        messages.error(request, 'Access denied. Admin privileges are required.')
        return redirect('core:home')

    if not user.is_verified:
        messages.error(request, 'Access denied. Your admin account is pending verification.')
        return redirect('core:home')

    # ------------------------------------------------------------------
    # 1) Verification Panel data
    # ------------------------------------------------------------------
    pending_users = User.objects.filter(
        is_verified=False
    ).exclude(
        role=User.Roles.ADMIN
    ).order_by('-date_joined')[:25]

    pending_missing_cases = MissingPerson.objects.filter(
        status='pending'
    ).order_by('-created_at')[:25]

    # For found persons we treat "unidentified" as needing attention
    pending_found_cases = FoundPerson.objects.filter(
        status='unidentified'
    ).order_by('-created_at')[:25]

    pending_matches = PotentialMatch.objects.filter(
        status='pending'
    ).select_related('missing_person', 'found_person').order_by('-created_at')[:50]

    # ------------------------------------------------------------------
    # 2) System Overview / Stats
    # ------------------------------------------------------------------
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_verified=True).count()
    unverified_users = total_users - verified_users

    total_missing = MissingPerson.objects.count()
    verified_missing = MissingPerson.objects.filter(status='verified').count()
    pending_missing_count = MissingPerson.objects.filter(status='pending').count()

    total_found = FoundPerson.objects.count()
    unidentified_found = FoundPerson.objects.filter(status='unidentified').count()

    # Matches confirmed today / this week
    now = timezone.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_today - timezone.timedelta(days=start_of_today.weekday())

    confirmed_matches_today = PotentialMatch.objects.filter(
        status='confirmed',
        reviewed_at__gte=start_of_today,
    ).count()

    confirmed_matches_this_week = PotentialMatch.objects.filter(
        status='confirmed',
        reviewed_at__gte=start_of_week,
    ).count()

    stats = {
        'total_users': total_users,
        'verified_users': verified_users,
        'unverified_users': unverified_users,
        'total_missing': total_missing,
        'verified_missing': verified_missing,
        'pending_missing': pending_missing_count,
        'total_found': total_found,
        'unidentified_found': unidentified_found,
        'confirmed_matches_today': confirmed_matches_today,
        'confirmed_matches_this_week': confirmed_matches_this_week,
    }

    # ------------------------------------------------------------------
    # 3) Activity & Audit logs
    # ------------------------------------------------------------------
    recent_activity = AuditLog.objects.select_related('user').order_by('-created_at')[:50]
    recent_logins = AuditLog.objects.filter(action='login').select_related('user').order_by('-created_at')[:20]

    context = {
        # Verification panel
        'pending_users': pending_users,
        'pending_missing_cases': pending_missing_cases,
        'pending_found_cases': pending_found_cases,
        'pending_matches': pending_matches,
        # Stats panel
        'stats': stats,
        # Activity panel
        'recent_activity': recent_activity,
        'recent_logins': recent_logins,
    }
    return render(request, 'core/dashboard.html', context)


# Authentication Views
def login_view(request):
    """Custom login view with enhanced form"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Check if user needs verification
            if not user.is_verified and user.role in [User.Roles.POLICE, User.Roles.NGO]:
                messages.warning(
                    request, 
                    f'Your {user.get_role_display()} account is pending verification. '
                    'Some features may be limited until verification is complete.'
                )
            else:
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            
            # Redirect to next page or dashboard
            next_page = request.GET.get('next')
            if next_page:
                return redirect(next_page)
            elif user.can_verify_cases():
                return redirect('core:dashboard')
            else:
                return redirect('core:home')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'core/auth/login.html', {'form': form})


def register_view(request):
    """Multi-step user registration with role selection"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Send different messages based on role
            if user.role == User.Roles.CITIZEN:
                messages.success(
                    request,
                    'Welcome to VanishVault! Your account is ready to use.'
                )
                # Auto-login citizens
                login(request, user)
                return redirect('core:home')
            else:
                messages.info(
                    request,
                    f'Your {user.get_role_display()} account has been created and is pending verification. '
                    'You\'ll be notified once verification is complete.'
                )
                return redirect('core:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/auth/register.html', {'form': form})


def logout_view(request):
    """Logout view with message"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


# Form Views
@login_required(login_url='core:login')
def report_missing_view(request):
    """Report a missing person - multi-step form"""
    if request.method == 'POST':
        form = ReportMissingForm(request.POST, request.FILES)
        if form.is_valid():
            missing_person = form.save(commit=False)
            missing_person.reporter = request.user
            missing_person.save()

            # After saving, generate embedding + run AI matching against
            # all FOUND reports. This only marks PotentialMatch entries;
            # admins must manually review/confirm them.
            uploaded_photo = request.FILES.get('photo')
            matching_service.create_report(
                report_type='missing',
                instance=missing_person,
                uploaded_photo=uploaded_photo,
                confidence_threshold=0.6,
            )
            
            messages.success(
                request,
                f'Missing person report submitted successfully. Case ID: {missing_person.case_id}'
            )
            return redirect('core:missing_detail', pk=missing_person.pk)
    else:
        form = ReportMissingForm()
    
    return render(request, 'core/forms/report_missing.html', {'form': form})


@login_required(login_url='core:login')
def report_found_view(request):
    """Report a found/unidentified person"""
    # Allow all authenticated users (including citizens) to report found persons.
    # Still require verification for higher-trust roles like NGO/Volunteer.
    if request.user.role in [User.Roles.NGO, User.Roles.VOLUNTEER] and not request.user.is_verified:
        messages.error(
            request,
            'Your NGO/Volunteer account is pending verification. You can report found persons after verification.'
        )
        return redirect('core:home')
    
    if request.method == 'POST':
        form = ReportFoundForm(request.POST, request.FILES)
        if form.is_valid():
            found_person = form.save()

            # After saving, generate embedding + run AI matching against
            # all MISSING reports. This only marks PotentialMatch entries;
            # admins must manually review/confirm them.
            uploaded_photo = request.FILES.get('photo')
            matching_service.create_report(
                report_type='found',
                instance=found_person,
                uploaded_photo=uploaded_photo,
                confidence_threshold=0.6,
            )
            
            messages.success(
                request,
                f'Found person report submitted successfully. Case ID: {found_person.case_id}'
            )
            return redirect('core:found_detail', pk=found_person.pk)
    else:
        form = ReportFoundForm()
    
    return render(request, 'core/forms/report_found.html', {'form': form})


@require_http_methods(["GET", "POST"])
def face_search_view(request):
    """Face search page for uploading photos and finding matches"""
    if request.method == 'POST':
        # Handle face search request
        from .face_recognition_utils import (
            extract_face_encoding_from_upload,
            find_matches,
            preprocess_image_for_ai,
            DEEPFACE_AVAILABLE,
            FACE_RECOGNITION_AVAILABLE
        )
        from .models import MissingPerson, FoundPerson
        import json
        import tempfile
        import os
        
        uploaded_file = request.FILES.get('image')
        search_type = request.POST.get('search_type', 'both')
        confidence_threshold = float(request.POST.get('confidence_threshold', 0.6))
        
        if not uploaded_file:
            return JsonResponse({'error': 'No image provided'}, status=400)
        
        # Determine which AI model is being used
        model_type = 'deepface' if DEEPFACE_AVAILABLE else 'face_recognition' if FACE_RECOGNITION_AVAILABLE else 'fallback'
        
        # Extract face encoding from uploaded image
        query_encoding = extract_face_encoding_from_upload(uploaded_file, use_deepface=DEEPFACE_AVAILABLE)
        
        if query_encoding is None:
            return JsonResponse({
                'error': 'No face detected in the uploaded image. Please try a clearer photo or ensure a face is visible.'
            }, status=400)
        
        # Get database photos based on search type
        database_encodings = []
        
        if search_type in ['both', 'missing']:
            missing_persons = MissingPerson.objects.filter(
                status='verified',
                photo__isnull=False
            ).exclude(photo='')
            
            for person in missing_persons:
                if person.photo:
                    try:
                        # Extract encoding from database photo
                        from .face_recognition_utils import extract_face_encoding
                        encoding = extract_face_encoding(person.photo.path)
                        if encoding is not None:
                            database_encodings.append((person, encoding))
                    except Exception as e:
                        print(f"Error processing {person.full_name}: {e}")
                        continue
        
        if search_type in ['both', 'found']:
            found_persons = FoundPerson.objects.filter(
                status='unidentified',
                photo__isnull=False
            ).exclude(photo='')
            
            for person in found_persons:
                if person.photo:
                    try:
                        from .face_recognition_utils import extract_face_encoding
                        encoding = extract_face_encoding(person.photo.path)
                        if encoding is not None:
                            database_encodings.append((person, encoding))
                    except Exception as e:
                        print(f"Error processing {person.full_name}: {e}")
                        continue
        
        # Find matches using AI-powered face matching
        matches = find_matches(
            query_encoding,
            database_encodings,
            threshold=confidence_threshold,
            max_results=20,
            model_type=model_type
        )
        
        # Format results
        results = []
        for match in matches:
            person = match['person']
            result = {
                'id': person.pk,
                'name': person.full_name if hasattr(person, 'full_name') else person.possible_name or 'Unidentified',
                'case_id': person.case_id,
                'confidence': match['confidence'],
                'distance': match['distance'],
                'age': person.age if hasattr(person, 'age') else person.estimated_age,
                'gender': person.get_gender_display() if hasattr(person, 'get_gender_display') else person.gender,
                'photo_url': person.photo.url if person.photo else None,
                'type': 'missing' if isinstance(person, MissingPerson) else 'found',
                'location': person.last_seen_location if hasattr(person, 'last_seen_location') else person.found_location,
                'date': str(person.last_seen_date) if hasattr(person, 'last_seen_date') else str(person.found_date),
            }
            results.append(result)
        
        return JsonResponse({
            'success': True,
            'matches': results,
            'total_matches': len(results),
            'ai_model': model_type  # Inform frontend which AI model was used
        })
    
    # GET request - show the face search page
    return render(request, 'core/face_search.html')


def access_policy(request):
    """Public page describing roles, access and verification policy"""
    return render(request, 'core/policy/access.html')


def report_sighting(request, person_id):
    """Handle sighting report submissions - allows anonymous reporting"""
    person = get_object_or_404(MissingPerson, pk=person_id)
    
    if request.method == 'POST':
        # Get form data
        location = request.POST.get('location')
        date = request.POST.get('date')
        time = request.POST.get('time')
        description = request.POST.get('description')
        reporter_name = request.POST.get('reporter_name', 'Anonymous')
        reporter_phone = request.POST.get('reporter_phone', '')
        reporter_email = request.POST.get('reporter_email', '')
        confidence_level = request.POST.get('confidence_level', 'medium')
        
        # Create and save the sighting
        from .models import Sighting
        sighting = Sighting.objects.create(
            missing_person=person,
            location=location,
            date=date,
            time=time,
            description=description,
            reporter_name=reporter_name,
            reporter_phone=reporter_phone,
            reporter_email=reporter_email,
            confidence_level=confidence_level,
            reported_by=request.user if request.user.is_authenticated else None
        )
        
        messages.success(request, 'Thank you for your report! Authorities have been notified and will investigate.')
        return redirect('core:missing_detail', pk=person_id)
    
    # If not a POST request, redirect to the person's detail page
    return redirect('core:missing_detail', pk=person_id)


@login_required(login_url='core:login')
def request_contact(request, person_id):
    """Handle contact request submissions"""
    person = get_object_or_404(MissingPerson, pk=person_id)
    
    if request.method == 'POST':
        # Get form data
        requester_name = request.POST.get('requester_name')
        requester_phone = request.POST.get('requester_phone')
        requester_email = request.POST.get('requester_email')
        reason = request.POST.get('reason')
        
        # Here you would typically:
        # 1. Save the contact request
        # 2. Send an email notification to the case reporter
        # 3. Notify the requester that their request has been received
        
        messages.success(request, 'Your contact request has been submitted. The case reporter will be notified.')
        return redirect('core:missing_detail', pk=person_id)
    
    # If not a POST request, redirect to the person's detail page
    return redirect('core:missing_detail', pk=person_id)
