from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('found/', views.found_list, name='found_list'),
    path('missing/<int:pk>/', views.missing_detail, name='missing_detail'),
    path('found/<int:pk>/', views.found_detail, name='found_detail'),
    path('about/', lambda r: __import__('django').shortcuts.render(r, 'about.html'), name='about'),
    path('contact/', lambda r: __import__('django').shortcuts.render(r, 'contact.html'), name='contact'),
]


