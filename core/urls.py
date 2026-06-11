from django.urls import path
from . import views
from . import api_views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('found/', views.found_list, name='found_list'),
    path('missing/<int:pk>/', views.missing_detail, name='missing_detail'),
    path('found/<int:pk>/', views.found_detail, name='found_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('roadmap/', views.roadmap, name='roadmap'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Forms
    path('report/missing/', views.report_missing_view, name='report_missing'),
    path('report/found/', views.report_found_view, name='report_found'),
    path('report/sighting/<int:person_id>/', views.report_sighting, name='report_sighting'),
    path('request-contact/<int:person_id>/', views.request_contact, name='request_contact'),
    
    # Face Search
    path('face-search/', views.face_search_view, name='face_search'),
    
    # API Endpoints
    path('api/face-search/', api_views.FaceSearchAPI.as_view(), name='api_face_search'),
    path('api/quick-match/', api_views.quick_face_match, name='api_quick_match'),
    
    # Admin Actions
    path('dashboard/match/<int:match_id>/confirm/', views.confirm_match, name='confirm_match'),
    path('dashboard/match/<int:match_id>/reject/', views.reject_match, name='reject_match'),
    path('dashboard/user/<int:user_id>/verify/', views.verify_user, name='verify_user'),
    path('dashboard/missing/<int:case_id>/verify/', views.verify_missing_case, name='verify_missing_case'),
    path('dashboard/found/<int:case_id>/verify/', views.verify_found_case, name='verify_found_case'),
    
    # Policy
    path('policy/access/', views.access_policy, name='access_policy'),
]
