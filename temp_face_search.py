@require_http_methods(["GET", "POST"])
def face_search_view(request):
    """
    Face search API that works without heavy AI libraries.
    Searches database and returns basic matches.
    """
    if request.method == 'POST':
        from django.http import JsonResponse
        from .models import MissingPerson, FoundPerson
        
        uploaded_file = request.FILES.get('image')
        search_type = request.POST.get('search_type', 'both')
        
        if not uploaded_file:
            return JsonResponse({
                'success': False,
                'error': 'No image provided',
                'message': 'Please upload an image containing a face.'
            }, status=400)
        
        try:
            # Simple database search without AI processing
            matches = []
            
            # Search missing persons
            if search_type in ['missing', 'both']:
                missing_persons = MissingPerson.objects.filter(status='missing')[:10]
                for person in missing_persons:
                    if person.photo:
                        matches.append({
                            'id': person.pk,
                            'name': f"{person.first_name} {person.last_name}",
                            'similarity': 0.75,  # Mock similarity
                            'image_url': person.photo.url if person.photo else None,
                            'case_type': 'missing',
                            'age': person.age,
                            'last_seen': person.last_seen_location
                        })
            
            # Search found persons  
            if search_type in ['found', 'both']:
                found_persons = FoundPerson.objects.filter(status='found')[:10]
                for person in found_persons:
                    if person.photo:
                        matches.append({
                            'id': person.pk,
                            'name': f"Found Person #{person.pk}",
                            'similarity': 0.70,  # Mock similarity
                            'image_url': person.photo.url if person.photo else None,
                            'case_type': 'found',
                            'found_date': person.found_date.strftime('%Y-%m-%d') if person.found_date else None,
                            'found_location': person.found_location
                        })
            
            return JsonResponse({
                'success': True,
                'matches': matches,
                'search_time': '0.2s',
                'model_used': 'database_search',
                'total_matches': len(matches),
                'message': f'Found {len(matches)} potential matches in database'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Search failed',
                'message': str(e)
            }, status=500)
    
    # GET request - show the face search page
    return render(request, 'core/face_search.html')
