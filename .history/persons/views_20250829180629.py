from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import MissingPerson, FoundPerson


def home(request):
    latest_missing = MissingPerson.objects.order_by('-created_at')[:6]
    latest_found = FoundPerson.objects.order_by('-created_at')[:6]
    return render(request, 'home.html', {
        'latest_missing': latest_missing,
        'latest_found': latest_found,
    })


def search(request):
    query = request.GET.get('q', '')
    gender = request.GET.get('gender', '')
    location = request.GET.get('location', '')
    age_min = request.GET.get('age_min', '')
    age_max = request.GET.get('age_max', '')

    results = MissingPerson.objects.all()
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

    return render(request, 'search.html', {
        'results': results,
        'query': query,
        'gender_val': gender,
        'location_val': location,
        'age_min_val': age_min,
        'age_max_val': age_max,
    })


def found_list(request):
    items = FoundPerson.objects.order_by('-created_at')
    gender = request.GET.get('gender')
    if gender:
        items = items.filter(gender=gender)
    return render(request, 'found_list.html', {'items': items})


def missing_detail(request, pk: int):
    person = get_object_or_404(MissingPerson, pk=pk)
    return render(request, 'missing_detail.html', {'person': person})


def found_detail(request, pk: int):
    person = get_object_or_404(FoundPerson, pk=pk)
    return render(request, 'found_detail.html', {'person': person})

# Create your views here.
