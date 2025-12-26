"""
Development-specific Django settings for retirement_planner project.

This settings file includes:
- Django Tailwind for CSS development
- Django Debug Toolbar for debugging
- Browser reload for live updates
- More verbose logging
"""

from .base import *

# Override DEBUG for development
DEBUG = True

# Development-specific installed apps
INSTALLED_APPS += [
    'tailwind',  # Django Tailwind for CSS development
    'theme',  # Your Tailwind theme app
    'django_browser_reload',  # Auto-reload browser on file changes
    'debug_toolbar',  # Django Debug Toolbar for debugging
]

# Tailwind Configuration
TAILWIND_APP_NAME = 'theme'
NPM_BIN_PATH = config('NPM_BIN_PATH', default='/usr/local/bin/npm')

# Browser reload middleware (add early for proper functioning)
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # Debug toolbar
    'django_browser_reload.middleware.BrowserReloadMiddleware',  # Browser reload
] + MIDDLEWARE

# Django Debug Toolbar Configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Development-specific security settings (more relaxed)
# These make development easier but should NEVER be used in production
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']  # Allow all hosts in dev

# Development email backend (prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# More verbose logging in development
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Disable template caching in development (see changes immediately)
for template_engine in TEMPLATES:
    template_engine['OPTIONS']['debug'] = True

print("🚀 Running in DEVELOPMENT mode with Tailwind enabled")
print("   - Django Debug Toolbar: Available at http://127.0.0.1:8000")
print("   - Tailwind dev server: Run 'python manage.py tailwind start' in a separate terminal")
print("   - Browser reload: Enabled (pages auto-refresh on changes)")
