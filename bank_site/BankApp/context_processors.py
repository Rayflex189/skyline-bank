# BankApp/context_processors.py
import os
from django.conf import settings

def site_icons(request):
    """Context processor that checks for icon files and provides fallbacks."""
    
    # Base icon paths (in /static/img/)
    icon_paths = {
        '16': '/static/img/logo-16x16.png',
        '32': '/static/img/logo-32x32.png',
        '72': '/static/img/logo-72x72.png',
        '96': '/static/img/logo-96x96.png',
        '128': '/static/img/logo-128x128.png',
        '144': '/static/img/logo-144x144.png',
        '152': '/static/img/logo-152x152.png',
        '180': '/static/img/logo-180x180.png',
        '192': '/static/img/logo-192x192.png',
        '384': '/static/img/logo-384x384.png',
        '512': '/static/img/logo-512x512.png',
        'favicon': '/static/img/favicon.ico',
        'screenshot': '/static/img/logo-screenshot.png',
        'original': '/static/img/logo.svg',
    }
    
    # Check which icons actually exist (for debugging/fallback logic)
    existing_icons = {}
    for key, path in icon_paths.items():
        full_path = os.path.join(settings.BASE_DIR, path.lstrip('/'))
        if os.path.exists(full_path):
            existing_icons[key] = path
        else:
            # Fallback to SVG if version doesn't exist
            existing_icons[key] = '/static/img/logo.svg'
    
    return {
        'site_name': 'Axos Bank',
        'theme_color': '#09090B',
        'manifest_path': '/static/manifest.json',
        'icons': icon_paths,  # Always return all paths (Django will handle 404s)
        'icons_exist': existing_icons,  # For debugging
        'has_all_icons': len(existing_icons) == len(icon_paths),  # Check if all created
    }