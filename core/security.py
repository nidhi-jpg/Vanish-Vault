"""
Security utilities for VanishVault authentication system.
Includes rate limiting, password validation, and audit logging.
"""

import time
import hashlib
import secrets
from datetime import datetime, timedelta
from django.core.cache import cache
from django.contrib.auth.signals import user_login_failed, user_logged_in, user_logged_out
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class LoginAttemptMonitor:
    """Monitor and limit login attempts to prevent brute force attacks."""
    
    @staticmethod
    def get_cache_key(identifier):
        """Generate cache key for login attempts."""
        return f"login_attempts:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    @staticmethod
    def record_failed_attempt(identifier):
        """Record a failed login attempt."""
        cache_key = LoginAttemptMonitor.get_cache_key(identifier)
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, timeout=3600)  # 1 hour expiry
        
        # Log the failed attempt
        logger.warning(f"Failed login attempt #{attempts} for: {identifier}")
        
        return attempts
    
    @staticmethod
    def is_locked_out(identifier):
        """Check if identifier is locked out due to too many failed attempts."""
        cache_key = LoginAttemptMonitor.get_cache_key(identifier)
        attempts = cache.get(cache_key, 0)
        
        # Lock out after 5 failed attempts for 30 minutes
        if attempts >= 5:
            lockout_key = f"locked_out:{cache_key}"
            if not cache.get(lockout_key):
                cache.set(lockout_key, True, timeout=1800)  # 30 minutes
                logger.warning(f"Account locked out due to failed attempts: {identifier}")
            return True
        
        return False
    
    @staticmethod
    def clear_attempts(identifier):
        """Clear failed login attempts after successful login."""
        cache_key = LoginAttemptMonitor.get_cache_key(identifier)
        cache.delete(cache_key)
        lockout_key = f"locked_out:{cache_key}"
        cache.delete(lockout_key)


class PasswordValidator:
    """Enhanced password validation for security."""
    
    @staticmethod
    def validate_password(password, user=None):
        """Validate password strength."""
        errors = []
        
        # Length requirement
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        
        # Complexity requirements
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter.")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter.")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit.")
        
        # Special character requirement
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character.")
        
        # Common password patterns
        if password.lower() in ['password', '12345678', 'qwerty', 'admin']:
            errors.append("Password is too common. Please choose a more secure password.")
        
        # Check if password contains username
        if user and user.username.lower() in password.lower():
            errors.append("Password cannot contain your username.")
        
        if errors:
            raise ValidationError(errors)
        
        return True


class SessionSecurity:
    """Session security utilities."""
    
    @staticmethod
    def generate_session_token():
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_session(request):
        """Validate session security."""
        # Check if session is too old
        session_age = time.time() - request.session.get('session_start', time.time())
        if session_age > 86400:  # 24 hours
            return False
        
        # Check for session hijacking
        if 'user_agent' not in request.session:
            request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        elif request.session['user_agent'] != request.META.get('HTTP_USER_AGENT', ''):
            return False
        
        return True
    
    @staticmethod
    def refresh_session(request):
        """Refresh session security parameters."""
        request.session['session_start'] = time.time()
        request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        request.session.modified = True


# Signal receivers for audit logging
@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    """Log failed login attempts."""
    username = credentials.get('username', 'unknown')
    ip_address = get_client_ip(request)
    
    # Record failed attempt
    attempts = LoginAttemptMonitor.record_failed_attempt(username)
    
    # Log the event
    logger.warning(f"Login failed for '{username}' from IP {ip_address} (attempt #{attempts})")
    
    # Check for potential brute force
    if attempts >= 3:
        logger.error(f"Potential brute force attack detected for '{username}' from IP {ip_address}")


@receiver(user_logged_in)
def log_user_logged_in(sender, user, request, **kwargs):
    """Log successful user login."""
    ip_address = get_client_ip(request)
    
    # Clear failed attempts
    LoginAttemptMonitor.clear_attempts(user.username)
    
    # Refresh session security
    SessionSecurity.refresh_session(request)
    
    # Log the event
    logger.info(f"User '{user.username}' ({user.get_role_display()}) logged in from IP {ip_address}")
    
    # Create audit log
    try:
        from .models import AuditLog
        AuditLog.objects.create(
            user=user,
            action='login',
            details=f'User logged in from IP {ip_address}'
        )
    except Exception as e:
        logger.error(f"Failed to create audit log for login: {e}")


@receiver(user_logged_out)
def log_user_logged_out(sender, user, request, **kwargs):
    """Log user logout."""
    if user:
        ip_address = get_client_ip(request)
        logger.info(f"User '{user.username}' logged out from IP {ip_address}")
        
        # Create audit log
        try:
            from .models import AuditLog
            AuditLog.objects.create(
                user=user,
                action='logout',
                details=f'User logged out from IP {ip_address}'
            )
        except Exception as e:
            logger.error(f"Failed to create audit log for logout: {e}")


def get_client_ip(request):
    """Get client IP address from request."""
    if request is None:
        return 'unknown'
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


class SecurityHeaders:
    """Security headers middleware utilities."""
    
    @staticmethod
    def get_security_headers():
        """Get security headers for responses."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }


def validate_email_domain(email):
    """Validate email domain against allowed domains."""
    if hasattr(settings, 'ALLOWED_EMAIL_DOMAINS'):
        domain = email.split('@')[-1].lower()
        if domain not in settings.ALLOWED_EMAIL_DOMAINS:
            raise ValidationError(f"Email domain '{domain}' is not allowed.")
    return True


def generate_verification_token():
    """Generate secure email verification token."""
    return secrets.token_urlsafe(32)


def check_suspicious_activity(request):
    """Check for suspicious activity patterns."""
    ip_address = get_client_ip(request)
    
    # Check for multiple rapid requests from same IP
    cache_key = f"requests:{ip_address}"
    request_count = cache.get(cache_key, 0) + 1
    cache.set(cache_key, request_count, timeout=60)  # 1 minute
    
    if request_count > 100:  # More than 100 requests per minute
        logger.warning(f"Suspicious activity detected from IP {ip_address}: {request_count} requests/minute")
        return True
    
    return False
