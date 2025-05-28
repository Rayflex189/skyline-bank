from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates a superuser if none exists'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpass')
            print(f"Creating superuser with email {email}...")
            User.objects.create_superuser(email=email, password=password)
        else:
            print("Superuser already exists. Skipping creation.")
