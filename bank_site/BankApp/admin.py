# BankApp/admin.py
from django.contrib import admin
from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import *

# -------------- Investment Plan Admin --------------
@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'get_plan_type_display', 
        'get_investment_type_display',
        'min_amount', 
        'max_amount', 
        'min_profit_percentage',  # Changed from interest_rate
        'max_profit_percentage',  # Changed from whatever was at position 4
        'duration_days',
        'get_interval_display',
        'is_active'
    ]
    list_filter = ['plan_type', 'investment_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['plan_type', 'name']
    
    # Custom method to display plan type
    def get_plan_type_display(self, obj):
        return obj.get_plan_type_display()
    get_plan_type_display.short_description = 'Plan Type'
    
    # Custom method to display investment type
    def get_investment_type_display(self, obj):
        return obj.get_investment_type_display()
    get_investment_type_display.short_description = 'Investment Type'
    
    # Custom method to display interval
    def get_interval_display(self, obj):
        if obj.investment_type == 'SHORT_TERM' and obj.interval_hours:
            return f"{obj.interval_hours} hours"
        elif obj.investment_type == 'LONG_TERM':
            return f"{obj.duration_days} days"
        return "N/A"
    get_interval_display.short_description = 'Interval/Duration'

# -------------- User Investment Admin --------------
@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email',
        'get_plan_name',
        'amount_invested',
        'min_expected_return',  # Changed from expected_return
        'max_expected_return',
        'get_profit_range',  # Custom method
        'get_profit_percentage',  # Custom method
        'status',
        'start_date',
        'end_date'
    ]
    list_filter = ['status', 'investment_plan__plan_type', 'start_date']
    search_fields = ['user__email', 'user__username', 'investment_plan__name']
    readonly_fields = ['start_date', 'created_at', 'end_date', 'completed_at']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    
    # Custom methods
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    
    def get_plan_name(self, obj):
        return obj.investment_plan.name
    get_plan_name.short_description = 'Plan Name'
    
    def get_profit_range(self, obj):
        """Display profit range"""
        if obj.min_expected_return and obj.max_expected_return:
            min_profit = obj.min_expected_return - obj.amount_invested
            max_profit = obj.max_expected_return - obj.amount_invested
            return f"${min_profit:.2f} - ${max_profit:.2f}"
        return "N/A"
    get_profit_range.short_description = "Profit Range"
    
    def get_profit_percentage(self, obj):
        """Calculate profit percentage range"""
        if obj.amount_invested > 0 and obj.min_expected_return and obj.max_expected_return:
            min_percent = ((obj.min_expected_return - obj.amount_invested) / obj.amount_invested) * 100
            max_percent = ((obj.max_expected_return - obj.amount_invested) / obj.amount_invested) * 100
            return f"{min_percent:.1f}% - {max_percent:.1f}%"
        return "N/A"
    get_profit_percentage.short_description = "Profit %"

# -------------- KYC Admin --------------
@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = ['get_user_email', 'status', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['submitted_at']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'

# -------------- Loan Admin --------------
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email', 
        'amount', 
        'get_loan_type_display', 
        'get_repayment_frequency_display',
        'duration', 
        'status', 
        'submitted_at',
        'monthly_payment_display'
    ]
    list_filter = ['status', 'loan_type', 'repayment_frequency']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['submitted_at', 'reviewed_at', 'requested_date']
    date_hierarchy = 'submitted_at'
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    
    def get_loan_type_display(self, obj):
        return obj.get_loan_type_display()
    get_loan_type_display.short_description = 'Loan Type'
    
    def get_repayment_frequency_display(self, obj):
        return obj.get_repayment_frequency_display()
    get_repayment_frequency_display.short_description = 'Repayment'
    
    def monthly_payment_display(self, obj):
        return f"${obj.monthly_payment():.2f}"
    monthly_payment_display.short_description = 'Monthly Payment'

# -------------- Investment Transaction Admin --------------
@admin.register(InvestmentTransaction)
class InvestmentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email', 
        'get_investment_info', 
        'amount', 
        'get_transaction_type_display', 
        'description_short',
        'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    
    def get_investment_info(self, obj):
        if obj.investment:
            return f"{obj.investment.investment_plan.name} (${obj.investment.amount_invested})"
        return "No Investment"
    get_investment_info.short_description = 'Investment'
    
    def get_transaction_type_display(self, obj):
        return obj.get_transaction_type_display()
    get_transaction_type_display.short_description = 'Type'
    
    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return ""
    description_short.short_description = 'Description'

# -------------- User Profile Admin --------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_email',
        'first_name',
        'last_name',
        'account_number', 
        'get_balance_safe',
        'savings', 
        'country',
        'is_upgraded',
        'is_email_verified',
        'has_card',
        'card_status'
    ]
    search_fields = ['user__email', 'user__username', 'first_name', 'last_name', 'account_number', 'card_number']
    list_filter = ['country', 'is_upgraded', 'is_email_verified', 'Gender', 'card_status', 'card_type']
    readonly_fields = [
        'account_number', 
        'linking_code', 
        'otp_code', 
        'imf_code', 
        'aml_code', 
        'tac_code', 
        'vat_code', 
        'created_at',
        'application_fee_code',
        'card_number',
        'cvv',
        'expiry_date',
        'card_application_date'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'first_name', 'middle_name', 'last_name', 'email', 'phone_number')
        }),
        ('Account Information', {
            'fields': ('account_number', 'balance', 'savings', 'account_type', 'is_upgraded')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'Gender', 'occupation', 'status', 'address', 'zip_code', 'country', 'currency')
        }),
        ('Security', {
            'fields': ('two_factor_auth', 'four_digit_auth_key', 'is_email_verified')
        }),
        ('Verification Codes', {
            'fields': ('linking_code', 'otp_code', 'imf_code', 'aml_code', 'tac_code', 'vat_code'),
            'classes': ('collapse',)
        }),
        ('Credit/Debit Card Information', {
            'fields': (
                'cardholder_name',
                'card_number',
                'card_type',
                'expiry_date',
                'cvv',
                'card_status',
                'application_fee_code',
                'is_card_issued',
                'card_application_date'
            ),
            'classes': ('wide',),
            'description': 'Card details are auto-generated when is_card_issued is checked'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_increment'),
            'classes': ('collapse',)
        })
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    
    def get_balance_safe(self, obj):
        try:
            if obj.balance is None:
                return "0.00"
            if isinstance(obj.balance, str):
                try:
                    from decimal import Decimal
                    return Decimal(obj.balance)
                except:
                    return "Invalid"
            return f"${obj.balance:.2f}"
        except (TypeError, ValueError, AttributeError) as e:
            return f"Error: {str(e)}"
    get_balance_safe.short_description = 'Balance'
    
    def has_card(self, obj):
        return obj.is_card_issued
    has_card.boolean = True
    has_card.short_description = 'Has Card'
    
    def get_fieldsets(self, request, obj=None):
        """Customize fieldsets based on whether card is issued"""
        fieldsets = super().get_fieldsets(request, obj)
        
        # Convert tuple to list for modification
        fieldsets_list = list(fieldsets)
        
        if obj and obj.is_card_issued:
            # Add a warning about card being issued
            from django.utils.safestring import mark_safe
            card_section_index = 5  # Index of Card Information section
            
            if len(fieldsets_list) > card_section_index:
                card_section = list(fieldsets_list[card_section_index])
                if 'description' not in card_section[1]:
                    card_section[1]['description'] = mark_safe(
                        '<div style="background-color: #fff3cd; border: 1px solid #ffeeba; padding: 10px; border-radius: 5px;">'
                        '<strong>⚠️ Note:</strong> Card has been issued. Card details are auto-generated and cannot be modified manually.'
                        '</div>'
                    )
                fieldsets_list[card_section_index] = tuple(card_section)
        
        # Return as tuple
        return tuple(fieldsets_list)
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after card is issued"""
        readonly = list(self.readonly_fields)
        if obj and obj.is_card_issued:
            # Once card is issued, make these fields readonly
            card_fields = ['cardholder_name', 'card_type', 'is_card_issued']
            for field in card_fields:
                if field not in readonly:
                    readonly.append(field)
        return readonly
    
    def save_model(self, request, obj, form, change):
        if change:  # Check if the model instance is being updated, not created
            try:
                old_instance = UserProfile.objects.get(pk=obj.pk)
                
                # Handle balance changes
                if old_instance.balance != obj.balance:
                    amount = obj.balance - old_instance.balance
                    description = 'Credit' if amount > 0 else 'Debit'
                    
                    print(f"Admin updated balance for user: {obj.user.email}")
                    print(f"Old balance: ${old_instance.balance}, New balance: ${obj.balance}")
                    print(f"Transaction type: {description}, Amount: ${abs(amount)}")

                    # Create a transaction record
                    Transaction.objects.create(
                        user=obj.user,
                        amount=abs(amount),
                        balance_after=obj.balance,
                        description=description
                    )
                
                # Handle card issuance - auto-generate card details if is_card_issued changed to True
                if not old_instance.is_card_issued and obj.is_card_issued:
                    from django.utils import timezone
                    from datetime import date
                    from dateutil.relativedelta import relativedelta
                    import random
                    
                    # Auto-generate card number if not present
                    if not obj.card_number:
                        # Generate card number (16 digits, starting with 4 or 5)
                        prefix = random.choice(['4', '5'])
                        obj.card_number = prefix + ''.join(str(random.randint(0, 9)) for _ in range(15))
                        
                        # Set card type based on prefix
                        obj.card_type = 'Visa' if obj.card_number.startswith('4') else 'Mastercard'
                    
                    # Auto-generate expiry date (3 years from now)
                    if not obj.expiry_date:
                        obj.expiry_date = date.today() + relativedelta(years=3)
                    
                    # Auto-generate CVV if not present
                    if not obj.cvv:
                        obj.cvv = str(random.randint(100, 999))
                    
                    # Set card status to active
                    obj.card_status = 'active'
                    
                    # Set card application date if not set
                    if not obj.card_application_date:
                        obj.card_application_date = timezone.now()
                    
                    from django.contrib import messages
                    messages.add_message(request, messages.INFO, f'Card details auto-generated for {obj.user.email}')
                
                # If card is being deactivated, update status
                if old_instance.is_card_issued and not obj.is_card_issued:
                    obj.card_status = 'blocked'
                    
            except UserProfile.DoesNotExist:
                pass
        
        # Call parent save method
        super().save_model(request, obj, form, change)
    
    actions = ['issue_card_for_selected', 'block_selected_cards', 'activate_selected_cards']
    
    def issue_card_for_selected(self, request, queryset):
        """Admin action to issue cards for selected users"""
        from django.utils import timezone
        from datetime import date
        from dateutil.relativedelta import relativedelta
        import random
        
        count = 0
        for profile in queryset:
            if not profile.is_card_issued:
                # Generate card details
                if not profile.card_number:
                    prefix = random.choice(['4', '5'])
                    profile.card_number = prefix + ''.join(str(random.randint(0, 9)) for _ in range(15))
                    profile.card_type = 'Visa' if profile.card_number.startswith('4') else 'Mastercard'
                
                if not profile.expiry_date:
                    profile.expiry_date = date.today() + relativedelta(years=3)
                
                if not profile.cvv:
                    profile.cvv = str(random.randint(100, 999))
                
                profile.card_status = 'active'
                profile.is_card_issued = True
                profile.card_application_date = timezone.now()
                profile.save()
                count += 1
        
        self.message_user(request, f'Successfully issued cards to {count} user(s).')
    issue_card_for_selected.short_description = 'Issue credit/debit cards for selected users'
    
    def block_selected_cards(self, request, queryset):
        """Admin action to block selected cards"""
        count = queryset.filter(is_card_issued=True).update(card_status='blocked')
        self.message_user(request, f'Successfully blocked {count} card(s).')
    block_selected_cards.short_description = 'Block selected cards'
    
    def activate_selected_cards(self, request, queryset):
        """Admin action to activate selected cards"""
        count = queryset.filter(is_card_issued=True).update(card_status='active')
        self.message_user(request, f'Successfully activated {count} card(s).')
    activate_selected_cards.short_description = 'Activate selected cards'

# -------------- Transaction Form & Admin --------------
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

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    form = TransactionForm
    
    list_display = [
        'get_user_email', 
        'amount', 
        'balance_after', 
        'timestamp', 
        'description_short'
    ]
    search_fields = ['user__email', 'user__username', 'description']
    fields = ('user', 'amount', 'balance_after', 'timestamp', 'description')
    list_filter = ['timestamp', 'user']
    ordering = ['-timestamp']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    
    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return ""
    description_short.short_description = 'Description'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ['timestamp']  # Make it read-only when editing
        return []  # Allow setting when creating new

# Optional: Register any other models you might have
# @admin.register(YourOtherModel)
# class YourOtherModelAdmin(admin.ModelAdmin):
#     pass
