from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import UserProfile, Transaction
from django.contrib.auth import get_user_model
from django.conf import settings


@receiver(post_save, sender=UserProfile)
def create_transaction_on_balance_update(sender, instance, **kwargs):
    if kwargs.get('created', False):
        # Skip creating transaction if the profile is just created
        return

    # Fetch the previous balance from the database
    try:
        old_instance = UserProfile.objects.get(pk=instance.pk)
    except UserProfile.DoesNotExist:
        return

    # Check if the balance has changed
    if old_instance.balance != instance.balance:
        amount = instance.balance - old_instance.balance
        description = 'Credit' if amount > 0 else 'Debit'

        print(f"Balance updated for user: {instance.user.username}")
        print(f"Old balance: {old_instance.balance}, New balance: {instance.balance}")
        print(f"Transaction type: {description}, Amount: {abs(amount)}")

        Transaction.objects.create(
            user=instance.user,
            amount=abs(amount),
            balance_after=instance.balance,
            description=description
        )


@receiver(post_migrate)
def create_superuser_after_migrate(sender, **kwargs):
    User = get_user_model()
    email = settings.SUPERUSER_EMAIL
    password = settings.SUPERUSER_PASSWORD

    if not User.objects.filter(email=email).exists():
        print(f"Creating superuser {email}")
        User.objects.create_superuser(email=email, password=password)
    else:
        print(f"Superuser {email} already exists.")
