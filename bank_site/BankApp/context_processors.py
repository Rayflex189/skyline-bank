# BankApp/context_processors.py
import os
from django.conf import settings

def site_icons(request):
    """Context processor that checks for icon files and provides fallbacks."""
    
    # Base icon paths (in /static/img/)
    icon_paths = {
        '16': '/static/img/blue-16x16.png',
        '32': '/static/img/blue-32x32.png',
        '72': '/static/img/blue-72x72.png',
        '96': '/static/img/blue-96x96.png',
        '128': '/static/img/blue-128x128.png',
        '144': '/static/img/blue-144x144.png',
        '152': '/static/img/blue-152x152.png',
        '180': '/static/img/blue-180x180.png',
        '192': '/static/img/blue-192x192.png',
        '384': '/static/img/blue-384x384.png',
        '512': '/static/img/blue-512x512.png',
        'favicon': '/static/img/favicon.ico',
        'screenshot': '/static/img/blue-screenshot.png',
        'original': '/static/img/blue.png',
    }
    
    # Check which icons actually exist (for debugging/fallback logic)
    existing_icons = {}
    for key, path in icon_paths.items():
        full_path = os.path.join(settings.BASE_DIR, path.lstrip('/'))
        if os.path.exists(full_path):
            existing_icons[key] = path
        else:
            # Fallback to original if resized version doesn't exist
            existing_icons[key] = '/static/img/blue.png'
    
    return {
        'site_name': 'SkyBridge Bank',
        'theme_color': '#1A4A7A',
        'manifest_path': '/static/manifest.json',
        'icons': icon_paths,  # Always return all paths (Django will handle 404s)
        'icons_exist': existing_icons,  # For debugging
        'has_all_icons': len(existing_icons) == len(icon_paths),  # Check if all created
    }