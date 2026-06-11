from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from .models import User


def role_required(allowed_roles):
    """
    Decorator to restrict access to specific user roles.
    
    Usage:
        @role_required(['police', 'admin'])
        def police_only_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request, 
                    f'Access denied. This feature requires {" or ".join(allowed_roles)} role.'
                )
                return redirect('core:home')
        return _wrapped_view
    return decorator


def police_required(view_func):
    """Decorator for police-only views"""
    return role_required([User.Roles.POLICE, User.Roles.ADMIN])(view_func)


def ngo_required(view_func):
    """Decorator for NGO-only views"""
    return role_required([User.Roles.NGO, User.Roles.ADMIN])(view_func)


def volunteer_required(view_func):
    """Decorator for volunteer+ views"""
    return role_required([User.Roles.VOLUNTEER, User.Roles.NGO, User.Roles.POLICE, User.Roles.ADMIN])(view_func)


def verified_required(view_func):
    """Decorator to require user verification"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_verified:
            return view_func(request, *args, **kwargs)
        else:
            messages.warning(
                request,
                'Your account is pending verification. Some features are limited.'
            )
            return redirect('core:home')
    return _wrapped_view


def admin_required(view_func):
    """Decorator for admin-only views"""
    return role_required([User.Roles.ADMIN])(view_func)
