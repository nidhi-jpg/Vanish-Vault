"""
API endpoints for VanishVault face matching system.
Provides real-time face search and matching capabilities.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.files.uploadedfile import InMemoryUploadedFile
import json
import base64
import io
from typing import Dict, List, Any

from .face_recognition_utils import (
    extract_face_encoding_from_upload,
    find_matches,
    DEEPFACE_AVAILABLE,
    FACE_RECOGNITION_AVAILABLE,
    classify_match_quality,
    preprocess_image_pil
)
from .models import MissingPerson, FoundPerson, PotentialMatch
from . import matching_service


@method_decorator(csrf_exempt, name='dispatch')
class FaceSearchAPI(View):
    """
    Real-time face search API endpoint.
    Supports both file upload and base64 image data.
    """
    
    def post(self, request):
        """Handle face search requests with enhanced matching."""
        try:
            # Parse request data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                image_data = data.get('image')
                search_type = data.get('search_type', 'both')
                confidence_threshold = float(data.get('confidence_threshold', 0.6))
                include_unreported = data.get('include_unreported', True)
                
                if not image_data:
                    return self._error_response('No image data provided')
                
                # Convert base64 to file
                try:
                    # Remove data URL prefix if present
                    if 'base64,' in image_data:
                        image_data = image_data.split('base64,')[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    uploaded_file = InMemoryUploadedFile(
                        io.BytesIO(image_bytes),
                        'image',
                        'search.jpg',
                        'image/jpeg',
                        len(image_bytes),
                        None
                    )
                except Exception as e:
                    return self._error_response(f'Invalid image data: {str(e)}')
            
            else:  # Form data
                uploaded_file = request.FILES.get('image')
                search_type = request.POST.get('search_type', 'both')
                confidence_threshold = float(request.POST.get('confidence_threshold', 0.6))
                include_unreported = request.POST.get('include_unreported', 'true').lower() == 'true'
                
                if not uploaded_file:
                    return self._error_response('No image provided')
            
            # Determine AI model
            model_info = self._get_model_info()
            
            # Extract face encoding
            query_encoding = extract_face_encoding_from_upload(
                uploaded_file, 
                use_deepface=DEEPFACE_AVAILABLE
            )
            
            if query_encoding is None:
                return self._error_response(
                    'No face detected',
                    suggestions=[
                        'Ensure the face is clearly visible',
                        'Try better lighting conditions',
                        'Avoid blurry or low-quality images',
                        'Face should not be too small or at extreme angles'
                    ]
                )
            
            # Get database encodings
            database_encodings = self._get_database_encodings(
                search_type=search_type,
                include_unreported=include_unreported
            )
            
            if not database_encodings:
                return self._success_response([], {
                    'total_matches': 0,
                    'message': 'No database entries found to search against'
                }, model_info)
            
            # Perform matching
            matches = find_matches(
                query_encoding,
                database_encodings,
                threshold=confidence_threshold,
                max_results=50,
                model_type=model_info['type']
            )
            
            # Format results
            results, summary = self._format_results(matches)
            
            # Create potential matches for high-confidence results
            self._create_potential_matches(matches, model_info['name'])
            
            return self._success_response(results, summary, model_info)
            
        except Exception as e:
            return self._error_response(f'Processing error: {str(e)}', status=500)
    
    def _get_model_info(self) -> Dict[str, str]:
        """Get information about the AI model being used."""
        if DEEPFACE_AVAILABLE:
            from django.conf import settings
            return {
                'type': 'deepface',
                'name': getattr(settings, 'DEEPFACE_MODEL', 'VGG-Face'),
                'capabilities': ['angle_invariant', 'lighting_normalization', 'multi_detector']
            }
        elif FACE_RECOGNITION_AVAILABLE:
            return {
                'type': 'face_recognition',
                'name': 'face_recognition',
                'capabilities': ['basic_angle_tolerance', 'standard_preprocessing']
            }
        else:
            return {
                'type': 'fallback',
                'name': 'fallback',
                'capabilities': ['dummy_mode']
            }
    
    def _get_database_encodings(self, search_type: str, include_unreported: bool) -> List:
        """Get face encodings from database based on search criteria."""
        database_encodings = []
        
        # Search missing persons
        if search_type in ['both', 'missing']:
            missing_persons = MissingPerson.objects.filter(
                status__in=['verified', 'pending'],
                photo__isnull=False
            ).exclude(photo='')
            
            for person in missing_persons:
                encoding = self._get_person_encoding(person)
                if encoding is not None:
                    database_encodings.append((person, encoding))
        
        # Search found persons
        if search_type in ['both', 'found']:
            found_persons = FoundPerson.objects.filter(
                photo__isnull=False
            ).exclude(photo='')
            
            if not include_unreported:
                found_persons = found_persons.filter(status='identified')
            
            for person in found_persons:
                encoding = self._get_person_encoding(person)
                if encoding is not None:
                    database_encodings.append((person, encoding))
        
        return database_encodings
    
    def _get_person_encoding(self, person):
        """Get face encoding for a person, using cached version if available."""
        try:
            # Try cached embedding first
            if person.face_embedding:
                encoding = matching_service._deserialize_embedding(person.face_embedding)
                if encoding is not None:
                    return encoding
            
            # Generate on-the-fly if not cached
            if person.photo and person.photo.path:
                from .face_recognition_utils import extract_face_encoding
                return extract_face_encoding(person.photo.path)
        except Exception as e:
            print(f"Error getting encoding for {person}: {e}")
        
        return None
    
    def _format_results(self, matches: List[Dict]) -> tuple:
        """Format matching results with enhanced information."""
        results = []
        high_confidence = 0
        medium_confidence = 0
        low_confidence = 0
        
        for match in matches:
            person = match['person']
            
            # Count confidence levels
            confidence = match['confidence']
            if confidence >= 80:
                high_confidence += 1
            elif confidence >= 65:
                medium_confidence += 1
            else:
                low_confidence += 1
            
            # Build result object
            result = {
                'id': person.pk,
                'name': self._get_person_name(person),
                'case_id': person.case_id,
                'confidence': confidence,
                'distance': match['distance'],
                'classification': match['classification'],
                'is_match': match['is_match'],
                'color': match['color'],
                'description': match['description'],
                'match_quality': match['match_quality'],
                'age': self._get_person_age(person),
                'gender': self._get_person_gender(person),
                'photo_url': person.photo.url if person.photo else None,
                'type': 'missing' if isinstance(person, MissingPerson) else 'found',
                'location': self._get_person_location(person),
                'date': self._get_person_date(person),
                'status': person.status,
            }
            
            # Add type-specific information
            if isinstance(person, MissingPerson):
                result['days_missing'] = person.days_missing
                result['reporter_relationship'] = person.reporter_relationship
            else:
                result['found_by_organization'] = person.found_by_organization
                result['contact_person'] = person.contact_person
            
            results.append(result)
        
        # Create summary
        summary = {
            'total_matches': len(results),
            'high_confidence_matches': high_confidence,
            'medium_confidence_matches': medium_confidence,
            'low_confidence_matches': low_confidence,
            'match_distribution': {
                'high': high_confidence,
                'medium': medium_confidence,
                'low': low_confidence
            }
        }
        
        return results, summary
    
    def _get_person_name(self, person) -> str:
        """Get person's name with fallback."""
        if hasattr(person, 'full_name'):
            return person.full_name or 'Unknown'
        elif hasattr(person, 'possible_name'):
            return person.possible_name or 'Unidentified'
        return 'Unknown'
    
    def _get_person_age(self, person) -> int:
        """Get person's age."""
        if hasattr(person, 'age'):
            return person.age
        elif hasattr(person, 'estimated_age'):
            return person.estimated_age
        return None
    
    def _get_person_gender(self, person) -> str:
        """Get person's gender."""
        if hasattr(person, 'get_gender_display'):
            return person.get_gender_display()
        return getattr(person, 'gender', 'Unknown')
    
    def _get_person_location(self, person) -> str:
        """Get person's location."""
        if hasattr(person, 'last_seen_location'):
            return person.last_seen_location
        elif hasattr(person, 'found_location'):
            return person.found_location
        return 'Unknown'
    
    def _get_person_date(self, person) -> str:
        """Get relevant date for person."""
        if hasattr(person, 'last_seen_date') and person.last_seen_date:
            return str(person.last_seen_date)
        elif hasattr(person, 'found_date') and person.found_date:
            return str(person.found_date)
        return 'Unknown'
    
    def _create_potential_matches(self, matches: List[Dict], ai_model: str):
        """Create PotentialMatch records for high-confidence results."""
        from django.utils import timezone
        
        for match in matches:
            # Only create for matches above medium confidence
            if match['confidence'] >= 65:
                person = match['person']
                
                # Determine if this is missing or found person
                if isinstance(person, MissingPerson):
                    missing_person = person
                    # Find corresponding found persons in database
                    found_persons = FoundPerson.objects.filter(
                        photo__isnull=False
                    ).exclude(face_embedding__isnull=True)
                    
                    for found_person in found_persons[:5]:  # Limit to prevent too many matches
                        # Check if match already exists
                        if not PotentialMatch.objects.filter(
                            missing_person=missing_person,
                            found_person=found_person
                        ).exists():
                            PotentialMatch.objects.create(
                                missing_person=missing_person,
                                found_person=found_person,
                                triggered_by='api_search',
                                distance=match['distance'],
                                confidence=match['confidence'],
                                ai_model=ai_model,
                                status='pending'
                            )
                elif isinstance(person, FoundPerson):
                    found_person = person
                    # Find corresponding missing persons in database
                    missing_persons = MissingPerson.objects.filter(
                        status__in=['verified', 'pending'],
                        photo__isnull=False
                    ).exclude(face_embedding__isnull=True)
                    
                    for missing_person in missing_persons[:5]:  # Limit to prevent too many matches
                        # Check if match already exists
                        if not PotentialMatch.objects.filter(
                            missing_person=missing_person,
                            found_person=found_person
                        ).exists():
                            PotentialMatch.objects.create(
                                missing_person=missing_person,
                                found_person=found_person,
                                triggered_by='api_search',
                                distance=match['distance'],
                                confidence=match['confidence'],
                                ai_model=ai_model,
                                status='pending'
                            )
    
    def _success_response(self, results: List, summary: Dict, model_info: Dict) -> JsonResponse:
        """Return successful response."""
        return JsonResponse({
            'success': True,
            'matches': results,
            'summary': summary,
            'ai_model': model_info['type'],
            'model_name': model_info['name'],
            'capabilities': model_info['capabilities'],
            'processing_info': {
                'angle_invariant': True,
                'lighting_normalization': True,
                'enhanced_preprocessing': True,
                'real_time_matching': True
            }
        })
    
    def _error_response(self, message: str, suggestions: List[str] = None, status: int = 400) -> JsonResponse:
        """Return error response."""
        response_data = {
            'success': False,
            'error': message,
        }
        
        if suggestions:
            response_data['suggestions'] = suggestions
        
        return JsonResponse(response_data, status=status)


@csrf_exempt
@require_http_methods(["POST"])
def quick_face_match(request):
    """
    Quick face matching endpoint for mobile apps and external services.
    Simplified version that returns only top matches.
    """
    try:
        # Parse request
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            image_data = data.get('image')
            max_results = int(data.get('max_results', 5))
        else:
            uploaded_file = request.FILES.get('image')
            max_results = int(request.POST.get('max_results', 5))
            image_data = None
        
        if not image_data and not uploaded_file:
            return JsonResponse({
                'success': False,
                'error': 'No image provided'
            }, status=400)
        
        # Convert to file if needed
        if image_data:
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            image_bytes = base64.b64decode(image_data)
            uploaded_file = InMemoryUploadedFile(
                io.BytesIO(image_bytes),
                'image',
                'quick_match.jpg',
                'image/jpeg',
                len(image_bytes),
                None
            )
        
        # Extract encoding and find matches
        query_encoding = extract_face_encoding_from_upload(
            uploaded_file,
            use_deepface=DEEPFACE_AVAILABLE
        )
        
        if query_encoding is None:
            return JsonResponse({
                'success': False,
                'error': 'No face detected'
            }, status=400)
        
        # Get all database encodings
        database_encodings = []
        
        # Add missing persons
        for person in MissingPerson.objects.filter(
            status='verified',
            photo__isnull=False
        ).exclude(photo=''):
            encoding = matching_service._deserialize_embedding(person.face_embedding)
            if encoding is not None:
                database_encodings.append((person, encoding))
        
        # Add found persons
        for person in FoundPerson.objects.filter(
            photo__isnull=False
        ).exclude(photo=''):
            encoding = matching_service._deserialize_embedding(person.face_embedding)
            if encoding is not None:
                database_encodings.append((person, encoding))
        
        if not database_encodings:
            return JsonResponse({
                'success': True,
                'matches': [],
                'message': 'No database entries found'
            })
        
        # Find matches
        model_type = 'deepface' if DEEPFACE_AVAILABLE else 'face_recognition'
        matches = find_matches(
            query_encoding,
            database_encodings,
            threshold=0.5,  # Lower threshold for quick search
            max_results=max_results,
            model_type=model_type
        )
        
        # Format simplified results
        results = []
        for match in matches:
            person = match['person']
            results.append({
                'id': person.pk,
                'name': person.full_name if hasattr(person, 'full_name') else person.possible_name or 'Unknown',
                'case_id': person.case_id,
                'confidence': match['confidence'],
                'type': 'missing' if isinstance(person, MissingPerson) else 'found',
                'photo_url': person.photo.url if person.photo else None
            })
        
        return JsonResponse({
            'success': True,
            'matches': results,
            'total_matches': len(results)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Processing error: {str(e)}'
        }, status=500)
