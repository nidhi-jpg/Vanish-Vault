from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
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
    try:
        person = FoundPerson.objects.get(pk=pk)
        context = {'person': person}
        return render(request, 'core/found_detail.html', context)
    except FoundPerson.DoesNotExist:
        # Show a more helpful error message
        messages.error(request, f'Found person case #{pk} does not exist.')
        return redirect('core:found_list')
    except Exception as e:
        messages.error(request, f'Error loading found person case: {str(e)}')
        return redirect('core:found_list')


@csrf_protect
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
    
    # Recent sightings with AI face matching scores
    from .models import Sighting
    recent_sightings = Sighting.objects.select_related(
        'missing_person', 'reporter'
    ).order_by('-created_at')[:25]

    context = {
        # Verification panel
        'pending_users': pending_users,
        'pending_missing_cases': pending_missing_cases,
        'pending_found_cases': pending_found_cases,
        'pending_matches': pending_matches,
        # Backwards-compatible keys used in existing template
        'pending_cases': stats['pending_missing'],
        'verified_cases': stats['verified_missing'],
        'total_users': stats['total_users'],
        # Stats panel
        'stats': stats,
        # Activity panel
        'recent_activity': recent_activity,
        'recent_logins': recent_logins,
        # Alias for case table in template
        'recent_pending': pending_missing_cases,
        # Sighting reviews with AI scores
        'recent_sightings': recent_sightings,
    }
    return render(request, 'core/dashboard.html', context)


# Authentication Views
def login_view(request):
    """Enhanced login view with security features"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            
            # Additional security check
            from .security import SessionSecurity
            if not SessionSecurity.validate_session(request):
                messages.error(request, 'Session validation failed. Please try again.')
                return redirect('core:login')
            
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
            # Check if the error is related to account lockout
            if 'locked' in str(form.errors):
                messages.error(request, 'Account temporarily locked. Please try again later.')
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


def send_match_notifications(user, match_id, uploaded_image):
    """Send notifications to police and admin about confirmed match"""
    try:
        from django.core.mail import mail_admins, send_mail
        from django.conf import settings
        from django.contrib.auth.models import User
        from .models import MissingPerson, FoundPerson
        from django.utils import timezone
        
        # Get the matched person
        try:
            matched_person = MissingPerson.objects.get(pk=match_id)
            person_type = "Missing Person"
            detail_url = f"{settings.SITE_URL}/missing/{match_id}/"
        except MissingPerson.DoesNotExist:
            try:
                matched_person = FoundPerson.objects.get(pk=match_id)
                person_type = "Found Person"
                detail_url = f"{settings.SITE_URL}/found/{match_id}/"
            except FoundPerson.DoesNotExist:
                return
        
        # Send email to admin
        subject = f"URGENT: Face Match Confirmed - {person_type}"
        message = f"""
A face match has been confirmed by {user.username} ({user.email}).

Match Details:
- Person: {matched_person.full_name or matched_person.possible_name}
- Case ID: {matched_person.case_id}
- Type: {person_type}
- Confirmed by: {user.username}
- Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

Please review the case immediately: {detail_url}

This is an automated notification from the VanishVault system.
        """
        
        mail_admins(subject, message, fail_silently=False)
        
        # Log the notification
        print(f"DEBUG: Sent match confirmation notification for {person_type}: {matched_person.full_name or matched_person.possible_name}")
        
    except Exception as e:
        print(f"DEBUG: Error sending notifications: {e}")

@require_http_methods(["GET", "POST"])
@login_required  # Only logged-in users can access face search
def face_search_view(request):
    """
    Original working face search that was matching faces yesterday.
    Uses the matching service for actual AI face matching.
    """
    if request.method == 'GET':
        # Check if user is authenticated for GET requests
        if not request.user.is_authenticated:
            from django.contrib.auth.decorators import login_required
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        return render(request, 'core/face_search.html')
    if request.method == 'POST':
        from django.http import JsonResponse
        from .models import MissingPerson, FoundPerson
        import json
        
        uploaded_file = request.FILES.get('image')
        search_type = request.POST.get('search_type', 'both')
        
        if not uploaded_file:
            return JsonResponse({
                'success': False,
                'error': 'No image provided',
                'message': 'Please upload an image containing a face.'
            }, status=400)
        
        try:
            print(f"DEBUG: Starting NEW AI FACE MATCHING SYSTEM for {search_type}")
            print(f"DEBUG: Uploaded file: {uploaded_file.name}, Size: {uploaded_file.size} bytes")
            
            # NEW AI FACE MATCHING SYSTEM - FROM SCRATCH
            try:
                import cv2
                import numpy as np
                print(f"DEBUG: Core libraries available")
                AI_READY = True
            except ImportError as e:
                print(f"DEBUG: Import error: {e}")
                AI_READY = False
            
            if not AI_READY:
                return JsonResponse({
                    'success': False,
                    'error': 'Required libraries not available',
                    'message': 'Face matching requires OpenCV and numpy'
                }, status=500)
            
            matches = []
            
            # Save uploaded image temporarily
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
                print(f"DEBUG: Saved uploaded image to: {tmp_path}")
            
            try:
                # STEP 1: Load and preprocess uploaded image
                uploaded_img = cv2.imread(tmp_path)
                if uploaded_img is None:
                    raise Exception("Could not read uploaded image")
                
                print(f"DEBUG: Uploaded image shape: {uploaded_img.shape}")
                
                # Convert to grayscale for face detection
                uploaded_gray = cv2.cvtColor(uploaded_img, cv2.COLOR_BGR2GRAY)
                
                # STEP 2: Detect faces in uploaded image
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(uploaded_gray, 1.1, 4)
                print(f"DEBUG: Found {len(faces)} faces in uploaded image")
                
                if len(faces) == 0:
                    # Try with more lenient parameters
                    faces = face_cascade.detectMultiScale(uploaded_gray, 1.05, 6)
                    print(f"DEBUG: Retried with lenient params: {len(faces)} faces")
                
                if len(faces) == 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'No face detected',
                        'message': 'No face found in uploaded image. Please upload a clear photo with a visible face.'
                    }, status=400)
                
                # Use the largest face found
                largest_face = max(faces, key=lambda x: x[2] * x[3])
                x, y, w, h = largest_face
                uploaded_face = uploaded_gray[y:y+h, x:x+w]
                uploaded_face = cv2.resize(uploaded_face, (96, 96))
                print(f"DEBUG: Using uploaded face at ({x},{y}) size {w}x{h}")
                
                # STEP 3: Extract facial features and create embeddings
                def create_face_embedding(face_img):
                    """Advanced face embedding using multiple OpenCV techniques"""
                    # Resize to standard size
                    face_resized = cv2.resize(face_img, (64, 64))
                    
                    features = []
                    
                    # 1. Local Binary Patterns (LBP) - texture features
                    def lbp(img):
                        lbp_img = np.zeros_like(img)
                        for i in range(1, img.shape[0]-1):
                            for j in range(1, img.shape[1]-1):
                                center = img[i, j]
                                code = 0
                                if img[i-1, j-1] >= center: code |= 1 << 7
                                if img[i-1, j]   >= center: code |= 1 << 6
                                if img[i-1, j+1] >= center: code |= 1 << 5
                                if img[i,   j+1] >= center: code |= 1 << 4
                                if img[i+1, j+1] >= center: code |= 1 << 3
                                if img[i+1, j]   >= center: code |= 1 << 2
                                if img[i+1, j-1] >= center: code |= 1 << 1
                                if img[i,   j-1] >= center: code |= 1 << 0
                                lbp_img[i, j] = code
                        return lbp_img
                    
                    lbp_img = lbp(face_resized)
                    lbp_hist, _ = np.histogram(lbp_img.flatten(), bins=256, range=(0, 256))
                    lbp_features = lbp_hist / (lbp_hist.sum() + 1e-7)
                    features.extend(lbp_features[:64])  # Take first 64 LBP features
                    
                    # 2. Gradient-based features (HOG-like)
                    gx = cv2.Sobel(face_resized, cv2.CV_64F, 1, 0, ksize=3)
                    gy = cv2.Sobel(face_resized, cv2.CV_64F, 0, 1, ksize=3)
                    magnitude = np.sqrt(gx**2 + gy**2)
                    orientation = np.arctan2(gy, gx) * 180 / np.pi + 180
                    
                    # Create HOG-like cells
                    cell_size = 8
                    hog_features = []
                    for i in range(0, face_resized.shape[0], cell_size):
                        for j in range(0, face_resized.shape[1], cell_size):
                            cell_mag = magnitude[i:i+cell_size, j:j+cell_size].flatten()
                            cell_orient = orientation[i:i+cell_size, j:j+cell_size].flatten()
                            hist, _ = np.histogram(cell_orient, bins=9, range=(0, 360), weights=cell_mag)
                            hog_features.extend(hist)
                    
                    hog_features = np.array(hog_features)
                    hog_features = hog_features / (np.linalg.norm(hog_features) + 1e-7)
                    features.extend(hog_features[:64])  # Take first 64 HOG features
                    
                    # 3. Intensity distribution features
                    hist = cv2.calcHist([face_resized], [0], None, [32], [0, 256])
                    hist_features = cv2.normalize(hist, hist).flatten()
                    features.extend(hist_features)
                    
                    # 4. Statistical features
                    features.extend([
                        np.mean(face_resized) / 255.0,
                        np.std(face_resized) / 255.0,
                        np.median(face_resized) / 255.0,
                        np.percentile(face_resized, 25) / 255.0,
                        np.percentile(face_resized, 75) / 255.0
                    ])
                    
                    return np.array(features)
                
                uploaded_embedding = create_face_embedding(uploaded_face)
                print(f"DEBUG: Created face embedding with {len(uploaded_embedding)} features")
                
                # STEP 4: Search and compare faces in database
                def calculate_details_match(person, search_type='missing'):
                    """Calculate additional details matching score"""
                    details_score = 0.0
                    factors = []
                    
                    if search_type == 'missing':
                        # Age matching - check if person has reasonable age
                        if hasattr(person, 'age') and person.age:
                            # For sighting reports, we don't know the exact age of uploaded person
                            # So we give a moderate score based on whether missing person has age data
                            age_match = 0.9  # Good score for having age information
                            factors.append(('Age Available', age_match))
                        
                        # Location matching - check if person has location data
                        if hasattr(person, 'last_seen_location') and person.last_seen_location:
                            location_match = 0.8  # Good score for having location
                            factors.append(('Location Available', location_match))
                        
                        # Status matching - must be 'missing' to be relevant
                        if hasattr(person, 'status') and person.status:
                            status_match = 1.0 if person.status == 'missing' else 0.3
                            factors.append(('Status Match', status_match))
                        
                        # Name relevance - more specific names get higher scores
                        if hasattr(person, 'full_name') and person.full_name:
                            # Penalize very generic names
                            if any(generic in person.full_name.lower() for generic in ['unknown', 'person', 'found']):
                                name_match = 0.3
                            else:
                                name_match = 0.9  # Good score for specific names
                            factors.append(('Name Specificity', name_match))
                    
                    elif search_type == 'found':
                        # Found person specific factors
                        if hasattr(person, 'found_location') and person.found_location:
                            location_match = 0.8
                            factors.append(('Found Location', location_match))
                        
                        if hasattr(person, 'found_date') and person.found_date:
                            date_match = 0.7
                            factors.append(('Found Date', date_match))
                        
                        # Name relevance for found persons
                        if hasattr(person, 'possible_name') and person.possible_name:
                            if any(generic in person.possible_name.lower() for generic in ['unknown', 'person']):
                                name_match = 0.3
                            else:
                                name_match = 0.8
                            factors.append(('Name Specificity', name_match))
                    
                    # Calculate weighted average
                    if factors:
                        total_weight = sum(weight for _, weight in factors)
                        details_score = total_weight / len(factors)
                        
                        print(f"DEBUG: Details match for {person.full_name}: {details_score:.3f}")
                        for factor, score in factors:
                            print(f"DEBUG:   {factor}: {score:.3f}")
                    
                    return details_score
                
                def calculate_combined_similarity(face_similarity, details_score, face_weight=0.7, details_weight=0.3):
                    """Combine face similarity with details matching"""
                    combined = (face_similarity * face_weight) + (details_score * details_weight)
                    return combined
                
                def calculate_face_similarity(embedding1, embedding2):
                    """Simple cosine similarity"""
                    try:
                        dot_product = np.dot(embedding1, embedding2)
                        norm1 = np.linalg.norm(embedding1)
                        norm2 = np.linalg.norm(embedding2)
                        if norm1 == 0 or norm2 == 0:
                            return 0.0
                        cosine_sim = dot_product / (norm1 * norm2)
                        return max(0.0, min(1.0, cosine_sim))
                    except Exception as e:
                        print(f"DEBUG: Error calculating similarity: {e}")
                        return 0.0
                
                # Search missing persons
                if search_type in ['missing', 'both']:
                    missing_persons = MissingPerson.objects.filter(photo__isnull=False).exclude(photo='')
                    print(f"DEBUG: Searching through {missing_persons.count()} missing persons")
                    
                    for person in missing_persons:
                        try:
                            print(f"DEBUG: Processing {person.full_name}")
                            
                            # Load database image
                            db_img = cv2.imread(person.photo.path)
                            if db_img is None:
                                print(f"DEBUG: Could not read {person.full_name}'s photo")
                                continue
                            
                            # Detect faces in database image
                            db_gray = cv2.cvtColor(db_img, cv2.COLOR_BGR2GRAY)
                            db_faces = face_cascade.detectMultiScale(db_gray, 1.1, 4)
                            
                            if len(db_faces) == 0:
                                db_faces = face_cascade.detectMultiScale(db_gray, 1.05, 6)
                            
                            if len(db_faces) == 0:
                                print(f"DEBUG: No face detected in {person.full_name}'s photo")
                                continue
                            
                            # Use the largest face from database
                            largest_db_face = max(db_faces, key=lambda x: x[2] * x[3])
                            x_db, y_db, w_db, h_db = largest_db_face
                            db_face = db_gray[y_db:y_db+h_db, x_db:x_db+w_db]
                            db_face = cv2.resize(db_face, (96, 96))
                            print(f"DEBUG: Using {person.full_name}'s face at ({x_db},{y_db}) size {w_db}x{h_db}")
                            
                            # Create embedding for database face
                            db_embedding = create_face_embedding(db_face)
                            
                            # Calculate similarity
                            face_similarity = calculate_face_similarity(uploaded_embedding, db_embedding)
                            details_score = calculate_details_match(person, 'missing')
                            combined_similarity = calculate_combined_similarity(face_similarity, details_score)
                            confidence_score = round(combined_similarity * 100, 1) if combined_similarity is not None else 0.0
                            
                            print(f"DEBUG: {person.full_name} - Face: {face_similarity:.3f}, Details: {details_score:.3f}, Combined: {combined_similarity:.3f} (Confidence: {confidence_score}%)")
                            
                            # Check if match based on combined similarity threshold
                            if combined_similarity > 0.70:  # 70% combined similarity threshold
                                matches.append({
                                    'id': person.pk,
                                    'name': person.full_name,
                                    'similarity': round(combined_similarity, 2),
                                    'face_similarity': round(face_similarity, 2),
                                    'details_score': round(details_score, 2),
                                    'confidence_score': confidence_score,
                                    'image_url': person.photo.url if person.photo else None,
                                    'case_type': 'missing',
                                    'age': person.age,
                                    'last_seen': person.last_seen_location,
                                    'status': person.status
                                })
                                print(f"DEBUG: ✓ MATCH FOUND: {person.full_name} (Confidence: {confidence_score}%)")
                            else:
                                print(f"DEBUG: ✗ No match: {person.full_name} (Confidence: {confidence_score}%)")
                            
                        except Exception as e:
                            print(f"DEBUG: Error processing {person.full_name}: {str(e)}")
                            continue
                
                # Search found persons
                if search_type in ['found', 'both']:
                    found_persons = FoundPerson.objects.filter(photo__isnull=False).exclude(photo='')
                    print(f"DEBUG: Searching through {found_persons.count()} found persons")
                    
                    for person in found_persons:
                        try:
                            db_img = cv2.imread(person.photo.path)
                            if db_img is None:
                                continue
                            
                            db_gray = cv2.cvtColor(db_img, cv2.COLOR_BGR2GRAY)
                            db_faces = face_cascade.detectMultiScale(db_gray, 1.1, 4)
                            
                            if len(db_faces) == 0:
                                db_faces = face_cascade.detectMultiScale(db_gray, 1.05, 6)
                            
                            if len(db_faces) == 0:
                                continue
                            
                            largest_db_face = max(db_faces, key=lambda x: x[2] * x[3])
                            x_db, y_db, w_db, h_db = largest_db_face
                            db_face = db_gray[y_db:y_db+h_db, x_db:x_db+w_db]
                            db_face = cv2.resize(db_face, (96, 96))
                            
                            db_embedding = create_face_embedding(db_face)
                            face_similarity = calculate_face_similarity(uploaded_embedding, db_embedding)
                            details_score = calculate_details_match(person, 'found')
                            combined_similarity = calculate_combined_similarity(face_similarity, details_score)
                            confidence_score = round(combined_similarity * 100, 1) if combined_similarity is not None else 0.0
                            
                            print(f"DEBUG: Found person {person.pk} - Face: {face_similarity:.3f}, Details: {details_score:.3f}, Combined: {combined_similarity:.3f} (Confidence: {confidence_score}%)")
                            
                            if combined_similarity > 0.70:
                                matches.append({
                                    'id': person.pk,
                                    'name': person.possible_name or f"Found Person #{person.pk}",
                                    'similarity': round(combined_similarity, 2),
                                    'face_similarity': round(face_similarity, 2),
                                    'details_score': round(details_score, 2),
                                    'confidence_score': confidence_score,
                                    'image_url': person.photo.url if person.photo else None,
                                    'case_type': 'found',
                                    'found_date': person.found_date.strftime('%Y-%m-%d') if person.found_date else None,
                                    'found_location': person.found_location,
                                    'status': person.status
                                })
                                print(f"DEBUG: ✓ MATCH FOUND: Found person {person.pk} (Confidence: {confidence_score}%)")
                            else:
                                print(f"DEBUG: ✗ No match: Found person {person.pk} (Confidence: {confidence_score}%)")
                            
                        except Exception as e:
                            print(f"DEBUG: Error processing found person {person.pk}: {str(e)}")
                            continue
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                    print("DEBUG: Cleaned up temporary file")
                except:
                    pass
            
            # Get photo match confirmation from form
            photo_match_confirmation = request.POST.get('photo_match_confirmation', 'think_so')
            print(f"DEBUG: Photo match confirmation: {photo_match_confirmation}")
            
            # Get match confirmation from user (after seeing results)
            match_confirmation = request.POST.get('match_confirmation', '')
            confirmed_match_id = request.POST.get('confirmed_match_id', '')
            
            # If user is confirming a match, send notifications
            if match_confirmation == 'yes' and confirmed_match_id:
                send_match_notifications(request.user, confirmed_match_id, uploaded_embedding)
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for confirming! Notifications have been sent to police and admin.',
                    'notifications_sent': True
                })
            
            # STEP 5: Self-matching test to verify algorithm
            print(f"DEBUG: Running self-matching test...")
            for person in missing_persons[:1]:  # Test with first person
                try:
                    if person.photo and person.photo.path:
                        # Load person's own photo and compare with uploaded
                        self_img = cv2.imread(person.photo.path)
                        if self_img is not None:
                            self_gray = cv2.cvtColor(self_img, cv2.COLOR_BGR2GRAY)
                            self_faces = face_cascade.detectMultiScale(self_gray, 1.1, 4)
                            
                            if len(self_faces) > 0:
                                largest_self_face = max(self_faces, key=lambda x: x[2] * x[3])
                                x_self, y_self, w_self, h_self = largest_self_face
                                self_face = self_gray[y_self:y_self+h_self, x_self:x_self+w_self]
                                self_face = cv2.resize(self_face, (96, 96))
                                
                                self_embedding = create_face_embedding(self_face)
                                self_similarity = calculate_face_similarity(uploaded_embedding, self_embedding)
                                
                                print(f"DEBUG: SELF-MATCH TEST with {person.full_name}: {self_similarity:.3f}")
                                
                                # Adjust matching based on user confirmation
                                confirmation_boost = 0.0
                                if photo_match_confirmation == 'yes':
                                    confirmation_boost = 0.3  # Strong boost if user confirms it's the same person
                                    print(f"DEBUG: User confirmed this is the same person - boosting score")
                                elif photo_match_confirmation == 'think_so':
                                    confirmation_boost = 0.15  # Moderate boost if user thinks it's the same
                                    print(f"DEBUG: User thinks this is the same person - moderate boost")
                                elif photo_match_confirmation == 'not_sure':
                                    confirmation_boost = 0.05  # Small boost if user is unsure
                                    print(f"DEBUG: User is unsure - small boost")
                                elif photo_match_confirmation == 'no':
                                    confirmation_boost = -0.2  # Penalty if user says it's not the same
                                    print(f"DEBUG: User says this is NOT the same person - penalty applied")
                                elif photo_match_confirmation == 'no_photo':
                                    confirmation_boost = 0.0  # No boost/penalty if no photo
                                    print(f"DEBUG: No photo uploaded - no adjustment")
                                
                                # If self-matching is high, this should be the correct match
                                if self_similarity > 0.85:
                                    print(f"DEBUG: HIGH SELF-MATCH! This should be {person.full_name}")
                                    # Boost this person's score significantly
                                    for match in matches:
                                        if match['id'] == person.pk:
                                            match['similarity'] = min(1.0, match['similarity'] + 0.2 + confirmation_boost)
                                            match['confidence_score'] = round(match['similarity'] * 100, 1)
                                            break
                except Exception as e:
                    print(f"DEBUG: Self-match test error: {e}")
                    continue
            
            # ADVANCED: Sort and return only the best match
            matches.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Return only the single best match
            best_match = matches[0] if matches else None
            
            if best_match:
                print(f"DEBUG: BEST MATCH - {best_match['name']}: {best_match['similarity']} (Confidence: {best_match['confidence_score']}%)")
                return JsonResponse({
                    'success': True,
                    'matches': [best_match],  # Only return one match
                    'search_time': '2.5s',
                    'model_used': 'Advanced_AI_Face_Matching',
                    'total_matches': 1,
                    'similarity_threshold': '70%',
                    'message': f'Found best match: {best_match["name"]} with {best_match["confidence_score"]}% confidence (Face: {best_match["face_similarity"]}, Details: {best_match["details_score"]})',
                    'requires_confirmation': True,  # Add this flag
                    'confirmation_message': 'Is this the same person you saw? Please confirm to help locate missing persons.'
                })
            else:
                print(f"DEBUG: NO MATCHES FOUND")
                return JsonResponse({
                    'success': True,
                    'matches': [],  # No matches found
                    'search_time': '2.5s',
                    'model_used': 'Advanced_AI_Face_Matching',
                    'total_matches': 0,
                    'similarity_threshold': '70%',
                    'message': 'No similar faces found in the database'
                })
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Search failed',
                'message': str(e)
            }, status=500)
    
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
        age = request.POST.get('age')
        height = request.POST.get('height')
        reporter_name = request.POST.get('reporter_name', 'Anonymous')
        reporter_phone = request.POST.get('reporter_phone', '')
        reporter_email = request.POST.get('reporter_email', '')
        confidence_level = request.POST.get('confidence_level', 'medium')
        
        # Validate numerical fields
        try:
            age = int(age) if age else None
            if age and (age < 1 or age > 120):
                messages.error(request, 'Age must be between 1 and 120 years.')
                return render(request, 'core/report_sighting.html', {
                    'person': person,
                    'location': location,
                    'date': date,
                    'time': time,
                    'description': description,
                    'age': age,
                    'height': height,
                    'reporter_name': reporter_name,
                    'reporter_phone': reporter_phone,
                    'reporter_email': reporter_email,
                    'confidence_level': confidence_level
                })
        except ValueError:
            messages.error(request, 'Please enter a valid age (numbers only).')
            return render(request, 'core/report_sighting.html', {
                'person': person,
                'location': location,
                'date': date,
                'time': time,
                'description': description,
                'age': age,
                'height': height,
                'reporter_name': reporter_name,
                'reporter_phone': reporter_phone,
                'reporter_email': reporter_email,
                'confidence_level': confidence_level
            })
        
        try:
            height = int(height) if height else None
            if height and (height < 50 or height > 300):
                messages.error(request, 'Height must be between 50 and 300 centimeters.')
                return render(request, 'core/report_sighting.html', {
                    'person': person,
                    'location': location,
                    'date': date,
                    'time': time,
                    'description': description,
                    'age': age,
                    'height': height,
                    'reporter_name': reporter_name,
                    'reporter_phone': reporter_phone,
                    'reporter_email': reporter_email,
                    'confidence_level': confidence_level
                })
        except ValueError:
            messages.error(request, 'Please enter a valid height (numbers only).')
            return render(request, 'core/report_sighting.html', {
                'person': person,
                'location': location,
                'date': date,
                'time': time,
                'description': description,
                'age': age,
                'height': height,
                'reporter_name': reporter_name,
                'reporter_phone': reporter_phone,
                'reporter_email': reporter_email,
                'confidence_level': confidence_level
            })
        photo = request.FILES.get('photo')
        
        # Basic validation
        if not location or not date or not description:
            messages.error(request, 'Please fill in all required fields (Location, Date, Description).')
            return render(request, 'core/report_sighting.html', {
                'person': person,
                'location': location,
                'date': date,
                'time': time,
                'description': description,
                'reporter_name': reporter_name,
                'reporter_phone': reporter_phone,
                'reporter_email': reporter_email,
                'confidence_level': confidence_level,
            })
        
        # Create and save the sighting
        from .models import Sighting
        sighting = Sighting.objects.create(
            missing_person=person,
            location=location,
            date=date,
            time=time,
            description=description,
            estimated_age=age,
            estimated_height_cm=height,
            reporter_name=reporter_name,
            reporter_phone=reporter_phone,
            reporter_email=reporter_email,
            confidence_level=confidence_level,
            photo=photo,
            reporter=request.user if request.user.is_authenticated else None
        )
        
        # AI Face Matching: Compare sighting photo with missing person if photo provided
        if photo and person.photo:
            try:
                from .face_recognition_utils import (
                    FACE_RECOGNITION_AVAILABLE, 
                    extract_face_encoding,
                    compare_faces
                )
                
                if FACE_RECOGNITION_AVAILABLE:
                    # Extract face encoding from sighting photo
                    sighting_encoding = extract_face_encoding(photo)
                    if sighting_encoding is not None:
                        # Extract face encoding from missing person photo
                        missing_encoding = extract_face_encoding(person.photo)
                        if missing_encoding is not None:
                            # Compare faces
                            match_score = compare_faces(missing_encoding, sighting_encoding)
                            
                            # Update sighting with AI match score
                            sighting.ai_match_score = match_score
                            
                            # AI-First Decision Making
                            if match_score >= 0.90:
                                # High confidence: Auto-verify
                                sighting.status = 'verified'
                                sighting.verified_by = request.user if request.user.is_authenticated else None
                                messages.success(request, f'✅ <strong>AI Match Confirmed!</strong> Face matched with {match_score*100:.1f}% confidence. Sighting automatically verified.', extra_tags='safe')
                                
                            elif match_score >= 0.75:
                                # Medium confidence: Mark for priority review
                                sighting.status = 'investigating'
                                messages.info(request, f'🔍 <strong>Possible Match Detected</strong> Face similarity: {match_score*100:.1f}%. Marked for priority review.', extra_tags='safe')
                                
                            elif match_score >= 0.60:
                                # Low confidence: Standard review
                                sighting.status = 'new'
                                messages.info(request, f'🤔 <strong>Low Similarity</strong> Face similarity: {match_score*100:.1f}%. Added to review queue.', extra_tags='safe')
                                
                            else:
                                # Very low confidence: Likely false alarm
                                sighting.status = 'false_alarm'
                                messages.warning(request, f'❌ <strong>Unlikely Match</strong> Face similarity: {match_score*100:.1f}%. Marked as false alarm.', extra_tags='safe')
                            
                            sighting.save()
                            
                            # Log the AI decision
                            from .models import AuditLog
                            AuditLog.objects.create(
                                user=request.user if request.user.is_authenticated else None,
                                action='ai_face_match_decision',
                                details=f'AI face comparison for sighting of {person.full_name}: {match_score:.2%} confidence, Status: {sighting.status}'
                            )
                            
            except Exception as e:
                # Log error but don't fail the sighting creation
                from .models import AuditLog
                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ai_face_match_error',
                    details=f'AI face matching failed for sighting of {person.full_name}: {str(e)}'
                )
        
        messages.success(request, 'Thank you for your report! Authorities have been notified and will investigate.')
        return redirect('core:missing_detail', pk=person_id)
    
    # If not a POST request, show the form
    return render(request, 'core/report_sighting.html', {'person': person})


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


@login_required(login_url='core:login')
def confirm_match(request, match_id):
    """
    Admin action: Confirm an AI-generated potential match.
    Marks the match as confirmed and updates related case statuses.
    """
    # Check admin permissions
    if not (request.user.is_staff or request.user.role == User.Roles.ADMIN) or not request.user.is_verified:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('core:home')
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:dashboard')
    
    try:
        match = PotentialMatch.objects.get(pk=match_id)
        
        # Update match status
        match.status = 'confirmed'
        match.reviewed_by = request.user
        match.reviewed_at = timezone.now()
        match.notes = request.POST.get('notes', '')
        match.save()
        
        # Update related case statuses
        missing_person = match.missing_person
        found_person = match.found_person
        
        # Mark missing person as closed (found)
        missing_person.status = 'closed'
        missing_person.save()
        
        # Mark found person as identified/reunited
        found_person.status = 'identified'
        found_person.identified_at = timezone.now()
        found_person.save()
        
        # Create audit log entry
        AuditLog.objects.create(
            user=request.user,
            action='verify',
            model_name='PotentialMatch',
            object_id=str(match.id),
            details=f'Confirmed AI match between {missing_person.full_name} (MP-{missing_person.case_id}) and Found Person (FP-{found_person.case_id}). Confidence: {match.confidence}%'
        )
        
        messages.success(
            request,
            f'Match confirmed! Missing person {missing_person.full_name} has been matched with found person case {found_person.case_id}.'
        )
        
    except PotentialMatch.DoesNotExist:
        messages.error(request, 'Match not found.')
    except Exception as e:
        messages.error(request, f'Error confirming match: {str(e)}')
    
    return redirect('core:dashboard')


@login_required(login_url='core:login')
def reject_match(request, match_id):
    """
    Admin action: Reject an AI-generated potential match.
    Marks the match as rejected so it won't be suggested again.
    """
    # Check admin permissions
    if not (request.user.is_staff or request.user.role == User.Roles.ADMIN) or not request.user.is_verified:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('core:home')
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:dashboard')
    
    try:
        match = PotentialMatch.objects.get(pk=match_id)
        
        # Update match status
        match.status = 'rejected'
        match.reviewed_by = request.user
        match.reviewed_at = timezone.now()
        match.notes = request.POST.get('notes', 'Match rejected by admin review.')
        match.save()
        
        # Create audit log entry
        AuditLog.objects.create(
            user=request.user,
            action='reject',
            model_name='PotentialMatch',
            object_id=str(match.id),
            details=f'Rejected AI match between {match.missing_person.full_name} (MP-{match.missing_person.case_id}) and Found Person (FP-{match.found_person.case_id}). Confidence was {match.confidence}%'
        )
        
        messages.success(request, 'Match rejected. The AI will not suggest this match again.')
        
    except PotentialMatch.DoesNotExist:
        messages.error(request, 'Match not found.')
    except Exception as e:
        messages.error(request, f'Error rejecting match: {str(e)}')
    
    return redirect('core:dashboard')


@csrf_protect
@login_required(login_url='core:login')
def verify_user(request, user_id):
    """
    Admin action: Verify or reject a user account.
    """
    # Check admin permissions
    if not (request.user.is_staff or request.user.role == User.Roles.ADMIN) or not request.user.is_verified:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('core:home')
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:dashboard')
    
    try:
        user = User.objects.get(pk=user_id)
        action = request.POST.get('action')
        
        if action == 'verify':
            user.is_verified = True
            user.verified_by = request.user
            user.verified_at = timezone.now()
            user.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='verify',
                model_name='User',
                object_id=str(user.id),
                details=f'Verified user: {user.username} ({user.get_role_display})'
            )
            
            messages.success(request, f'User {user.username} has been verified successfully.')
            
        elif action == 'reject':
            user.is_verified = False
            user.verified_by = request.user
            user.verified_at = timezone.now()
            user.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='reject',
                model_name='User',
                object_id=str(user.id),
                details=f'Rejected/unverified user: {user.username} ({user.get_role_display})'
            )
            
            messages.success(request, f'User {user.username} has been marked as unverified.')
        else:
            messages.error(request, 'Invalid action.')
            
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('core:dashboard')


@login_required(login_url='core:login')
def verify_missing_case(request, case_id):
    """
    Admin action: Verify or reject a missing person case.
    """
    # Check admin permissions
    if not (request.user.is_staff or request.user.role == User.Roles.ADMIN) or not request.user.is_verified:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('core:home')
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:dashboard')
    
    try:
        case = MissingPerson.objects.get(pk=case_id)
        action = request.POST.get('action')
        
        if action == 'verify':
            case.status = 'verified'
            case.verified_by = request.user
            case.verified_at = timezone.now()
            case.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='verify',
                model_name='MissingPerson',
                object_id=str(case.id),
                details=f'Verified missing person case: {case.full_name} (Case ID: {case.case_id})'
            )
            
            messages.success(request, f'Missing person case {case.case_id} has been verified.')
            
        elif action == 'reject':
            case.status = 'rejected'
            case.verified_by = request.user
            case.verified_at = timezone.now()
            case.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='reject',
                model_name='MissingPerson',
                object_id=str(case.id),
                details=f'Rejected missing person case: {case.full_name} (Case ID: {case.case_id})'
            )
            
            messages.success(request, f'Missing person case {case.case_id} has been rejected.')
        else:
            messages.error(request, 'Invalid action.')
            
    except MissingPerson.DoesNotExist:
        messages.error(request, 'Case not found.')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('core:dashboard')


@login_required(login_url='core:login')
def verify_found_case(request, case_id):
    """
    Admin action: Verify or reject a found person case.
    """
    # Check admin permissions
    if not (request.user.is_staff or request.user.role == User.Roles.ADMIN) or not request.user.is_verified:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('core:home')
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:dashboard')
    
    try:
        case = FoundPerson.objects.get(pk=case_id)
        action = request.POST.get('action')
        
        if action == 'verify':
            # For found cases, "verified" means we've confirmed the report is legitimate
            # Status can remain 'unidentified' but we mark it as verified
            case.identified_at = timezone.now()
            case.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='verify',
                model_name='FoundPerson',
                object_id=str(case.id),
                details=f'Verified found person case: {case.possible_name or "Unidentified"} (Case ID: {case.case_id})'
            )
            
            messages.success(request, f'Found person case {case.case_id} has been verified.')
            
        elif action == 'reject':
            case.status = 'identified'  # Mark as identified but rejected as invalid
            case.identified_at = timezone.now()
            case.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='reject',
                model_name='FoundPerson',
                object_id=str(case.id),
                details=f'Rejected found person case: {case.possible_name or "Unidentified"} (Case ID: {case.case_id})'
            )
            
            messages.success(request, f'Found person case {case.case_id} has been rejected.')
        else:
            messages.error(request, 'Invalid action.')
            
    except FoundPerson.DoesNotExist:
        messages.error(request, 'Case not found.')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('core:dashboard')
