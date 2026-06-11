from django.shortcuts import render, redirect
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
    results = MissingPerson.objects.all()
    if query:
        results = results.filter(full_name__icontains=query)
    gender = request.GET.get('gender')
    if gender:
        results = results.filter(gender=gender)
    return render(request, 'search.html', {'results': results, 'query': query})


def found_list(request):
    items = FoundPerson.objects.order_by('-created_at')
    gender = request.GET.get('gender')
    if gender:
        items = items.filter(gender=gender)
    return render(request, 'found_list.html', {'items': items})

# Create your views here.
