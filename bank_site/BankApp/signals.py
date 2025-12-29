from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from .models import UserProfile, Transaction

User = get_user_model()


# Automatically create a profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, balance=0)


# Track balance changes and send alerts
@receiver(pre_save, sender=UserProfile)
def track_balance_changes(sender, instance, **kwargs):
    if not instance.pk:
        # Skip if profile is new
        return

    # Fetch old instance from the database
    old_instance = UserProfile.objects.filter(pk=instance.pk).first()
    if not old_instance:
        return

    old_balance = old_instance.balance
    new_balance = instance.balance

    if new_balance != old_balance:
        # Save the difference in the instance to use in post_save
        instance._balance_diff = new_balance - old_balance
        instance._old_balance = old_balance
        instance._description = 'Credit' if new_balance > old_balance else 'Debit'


@receiver(post_save, sender=UserProfile)
def create_transaction_and_send_email(sender, instance, created, **kwargs):
    # Skip new profiles
    if created:
        return

    # Check if pre_save stored balance change
    if hasattr(instance, '_balance_diff') and instance._balance_diff != 0:
        amount = abs(instance._balance_diff)
        description = instance._description
        old_balance = instance._old_balance
        new_balance = instance.balance
        currency = getattr(instance, 'currency', 'NGN')  # Default to NGN

        # Create transaction
        Transaction.objects.create(
            user=instance.user,
            amount=amount,
            balance_after=new_balance,
            description=description
        )

        # Send email alert
        subject = f"💰 Your account has been {description.lower()}ed"
        message = f"""
Hi {instance.user.email},

Your account has been {description.lower()}ed with: {currency} {amount:,.2f}
Your new balance is: {currency} {new_balance:,.2f}

Thank you for banking with us!
Skybridge Bank Security Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=False,
        )

        print(f"Balance updated for user: {instance.user.username}")
        print(f"{description}: {currency}{amount:,.2f} | New Balance: {currency}{new_balance:,.2f}")
