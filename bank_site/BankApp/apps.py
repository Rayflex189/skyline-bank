from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

class BankappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'BankApp'

    def ready(self):
        try:
            User = get_user_model()
            if not User.objects.filter(email=settings.SUPERUSER_EMAIL).exists():
                User.objects.create_superuser(
                    email=settings.SUPERUSER_EMAIL,
                    password=settings.SUPERUSER_PASSWORD
                )
        except (OperationalError, ProgrammingError):
            # Avoid errors during migration or before DB is ready
            pass
