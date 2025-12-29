from django.contrib import admin
from django import forms
from django.utils import timezone
from .models import Transaction
from datetime import timedelta
from .models import *

@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'min_amount', 'max_amount', 'interest_rate', 'duration_days', 'is_active']
    list_filter = ['plan_type', 'is_active']
    search_fields = ['name']

@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'investment_plan', 'amount_invested', 'expected_return', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'investment_plan']
    search_fields = ['user__username', 'investment_plan__name']

from django.contrib import admin
from .models import KYC, Loan

@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'submitted_at')
    list_filter = ('status',)

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'loan_type', 'status', 'submitted_at')
    list_filter = ('status', 'loan_type')


@admin.register(InvestmentTransaction)
class InvestmentTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'investment', 'amount', 'transaction_type', 'created_at']
    list_filter = ['transaction_type']
    search_fields = ['user__username']
    
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_number', 'otp_code', 'imf_code', 'aml_code', 'tac_code', 'vat_code', 'linking_code', 'balance']  # Include balance in the admin list
    search_fields = ['user__username']  # Search by username

    def save_model(self, request, obj, form, change):
        if change:  # Check if the model instance is being updated, not created
            try:
                old_instance = UserProfile.objects.get(pk=obj.pk)
                if old_instance.balance != obj.balance:
                    amount = obj.balance - old_instance.balance
                    description = 'Credit' if amount > 0 else 'Debit'
                    
                    # Print statements for debugging
                    print(f"Admin updated balance for user: {obj.user.username}")
                    print(f"Old balance: {old_instance.balance}, New balance: {obj.balance}")
                    print(f"Transaction type: {description}, Amount: {abs(amount)}")

                    # Create a transaction record
                    Transaction.objects.create(
                        user=obj.user,
                        amount=abs(amount),  # Use absolute value for amount
                        balance_after=obj.balance,
                        description=description
                    )
            except UserProfile.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)


from django import forms
from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import Transaction

# ---- Simple Form Without Custom Widget ----
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = '__all__'
    
    def clean_timestamp(self):
        ts = self.cleaned_data.get("timestamp")
        
        if not ts:
            return ts
            
        # Check 1-year limit
        one_year_ago = timezone.now() - timedelta(days=365)
        if ts < one_year_ago:
            raise forms.ValidationError("You cannot backdate a transaction more than 1 year.")
        
        return ts


# ---- Admin Panel ----
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    form = TransactionForm
    
    list_display = ['user', 'amount', 'balance_after', 'timestamp', 'description']
    search_fields = ['user__username', 'description']
    fields = ('user', 'amount', 'balance_after', 'timestamp', 'description')
    list_filter = ['timestamp', 'user']
    ordering = ['-timestamp']
    
    # Make timestamp read-only in the list view for safety
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ['timestamp']  # Make it read-only when editing
        return []  # Allow setting when creating new


class YourModelAdmin(admin.ModelAdmin):
    list_display = ('image_display',)

    def image_display(self, obj):
        return obj.image.url if obj.image else None