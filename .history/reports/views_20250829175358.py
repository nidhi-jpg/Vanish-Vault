from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django import forms
from persons.models import MissingPerson


class ReportMissingForm(forms.ModelForm):
    class Meta:
        model = MissingPerson
        fields = ['full_name', 'age', 'gender', 'last_seen_location', 'last_seen_date', 'description', 'photo']


@login_required(login_url='/accounts/login/')
def report_missing(request):
    if request.method == 'POST':
        form = ReportMissingForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ReportMissingForm()
    return render(request, 'report_missing.html', {'form': form})

# Create your views here.
