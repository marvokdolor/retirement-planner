"""
Production-specific Django settings for retirement_planner project.

This settings file:
- Excludes Tailwind (CSS is pre-compiled)
- Enables security features
- Optimizes for performance
- Uses production-grade email backend
"""

from .base import *

# Override DEBUG for production
DEBUG = False

# Production must have explicit ALLOWED_HOSTS (no wildcards)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

# Ensure ALLOWED_HOSTS is set in production
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must be set in production environment via .env file")

# NO Tailwind or debug tools in production
# INSTALLED_APPS only contains what's in base.py

# Security Settings for Production
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Trust Railway's proxy for HTTPS (prevents redirect loop)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HTTP Strict Transport Security (HSTS)
# Tells browsers to only access site via HTTPS for next year
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Redirect all HTTP to HTTPS (only in production with proper SSL)
# Note: Railway handles SSL termination, so we don't need this
# SECURE_SSL_REDIRECT = True  # Commented out - Railway uses proxy

# Production email backend (must be configured via environment variables)
# Auto-fallback to console backend if SMTP not configured
if config('EMAIL_HOST', default=''):
    EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
    print("📧 Email: Using SMTP backend")
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("⚠️  WARNING: EMAIL_HOST not configured. Using console backend (emails printed to logs).")

# Production-specific logging (less verbose, focus on errors)
LOGGING['root']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['django.request']['level'] = 'ERROR'

print("🔒 Running in PRODUCTION mode")
print("   - DEBUG: False")
print("   - Tailwind: Disabled (using pre-compiled CSS)")
print("   - Security: Enhanced (HSTS, secure cookies, XSS protection)")
