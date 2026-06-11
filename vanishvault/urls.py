"""vanishvault URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core import views as core_views

urlpatterns = [
    # Core app routes (must be first for proper URL resolution)
    path('', include('core.urls')),
    
    # Legacy dashboard verification endpoints (kept for backward compatibility)
    # Must be placed BEFORE the Django admin route so /admin/* doesn't get swallowed.
    path('admin/match/<int:match_id>/confirm/', core_views.confirm_match, name='legacy_confirm_match'),
    path('admin/match/<int:match_id>/reject/', core_views.reject_match, name='legacy_reject_match'),
    path('admin/user/<int:user_id>/verify/', core_views.verify_user, name='legacy_verify_user'),
    path('admin/missing/<int:case_id>/verify/', core_views.verify_missing_case, name='legacy_verify_missing_case'),
    path('admin/found/<int:case_id>/verify/', core_views.verify_found_case, name='legacy_verify_found_case'),
    
    # Django admin site
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
