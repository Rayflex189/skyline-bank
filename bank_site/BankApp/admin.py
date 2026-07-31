from django.contrib import admin
from django import forms
from django.utils import timezone
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
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
        'min_profit_percentage',
        'max_profit_percentage',
        'duration_days',
        'get_interval_display',
        'is_active'
    ]
    list_filter = ['plan_type', 'investment_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['plan_type', 'name']
    
    def get_plan_type_display(self, obj):
        return obj.get_plan_type_display()
    get_plan_type_display.short_description = 'Plan Type'
    
    def get_investment_type_display(self, obj):
        return obj.get_investment_type_display()
    get_investment_type_display.short_description = 'Investment Type'
    
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
        'min_expected_return',
        'max_expected_return',
        'get_profit_range',
        'get_profit_percentage',
        'status',
        'start_date',
        'end_date'
    ]
    list_filter = ['status', 'investment_plan__plan_type', 'start_date']
    search_fields = ['user__email', 'user__username', 'investment_plan__name']
    readonly_fields = ['start_date', 'created_at', 'end_date', 'completed_at']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    
    def get_plan_name(self, obj):
        return obj.investment_plan.name
    get_plan_name.short_description = 'Plan Name'
    
    def get_profit_range(self, obj):
        if obj.min_expected_return and obj.max_expected_return:
            min_profit = obj.min_expected_return - obj.amount_invested
            max_profit = obj.max_expected_return - obj.amount_invested
            return f"${min_profit:.2f} - ${max_profit:.2f}"
        return "N/A"
    get_profit_range.short_description = "Profit Range"
    
    def get_profit_percentage(self, obj):
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
        'linking_code_display', 
        'otp_code_display', 
        'imf_code_display', 
        'aml_code_display', 
        'tac_code_display', 
        'vat_code_display', 
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
        ('Verification Codes (click Regenerate to create a new code)', {
            'fields': ('linking_code_display', 'otp_code_display', 'imf_code_display', 
                       'aml_code_display', 'tac_code_display', 'vat_code_display'),
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
    
    # ---------- Custom URL for regeneration ----------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:user_id>/regenerate/<str:code_type>/',
                self.admin_site.admin_view(self.regenerate_code),
                name='regenerate_user_code',
            ),
        ]
        return custom_urls + urls
    
    def regenerate_code(self, request, user_id, code_type):
        """Regenerate a specific code for the given user profile."""
        profile = get_object_or_404(UserProfile, pk=user_id)
        code_map = {
            'linking_code': (generate_code, 'linking_code'),
            'otp_code': (generate_otp, 'otp_code'),
            'imf_code': (generate_iban, 'imf_code'),  # Use IBAN generation
            'aml_code': (generate_aml, 'aml_code'),
            'tac_code': (generate_tac, 'tac_code'),
            'vat_code': (generate_vat, 'vat_code'),
        }
        if code_type not in code_map:
            self.message_user(request, f"Unknown code type: {code_type}", level='ERROR')
            return redirect('admin:BankApp_userprofile_change', user_id)
        
        generator, field_name = code_map[code_type]
        if field_name == 'imf_code':
            # For IBAN, we need the country
            new_code = generator(profile.country) if profile.country else generate_iban('XX')
        else:
            new_code = generator()
        setattr(profile, field_name, new_code)
        profile.save()
        self.message_user(request, f"{code_type.replace('_', ' ').title()} regenerated successfully!")
        return redirect('admin:BankApp_userprofile_change', user_id)
    
    # ---------- Display methods with regenerate button ----------
    def _code_display(self, obj, code_field, display_name):
        """Helper to create a formatted code with regenerate button."""
        code = getattr(obj, code_field)
        url = reverse('admin:regenerate_user_code', args=[obj.pk, code_field])
        return format_html(
            '<span style="display:inline-block; min-width:120px;">{}</span> '
            '<a href="{}" class="button" style="padding:2px 8px; background:#79aec8; color:white; '
            'border-radius:4px; text-decoration:none; margin-left:8px;">Regenerate</a>',
            code,
            url
        )
    
    def linking_code_display(self, obj):
        return self._code_display(obj, 'linking_code', 'Linking Code')
    linking_code_display.short_description = 'Linking Code'
    
    def otp_code_display(self, obj):
        return self._code_display(obj, 'otp_code', 'OTP Code')
    otp_code_display.short_description = 'OTP Code'
    
    def imf_code_display(self, obj):
        return self._code_display(obj, 'imf_code', 'IMF Code (IBAN)')
    imf_code_display.short_description = 'IMF Code (IBAN)'
    
    def aml_code_display(self, obj):
        return self._code_display(obj, 'aml_code', 'AML Code')
    aml_code_display.short_description = 'AML Code'
    
    def tac_code_display(self, obj):
        return self._code_display(obj, 'tac_code', 'TAC Code')
    tac_code_display.short_description = 'TAC Code'
    
    def vat_code_display(self, obj):
        return self._code_display(obj, 'vat_code', 'VAT Code')
    vat_code_display.short_description = 'VAT Code'
    
    # ---------- Existing methods ----------
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
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets_list = list(fieldsets)
        if obj and obj.is_card_issued:
            from django.utils.safestring import mark_safe
            card_section_index = 5
            if len(fieldsets_list) > card_section_index:
                card_section = list(fieldsets_list[card_section_index])
                if 'description' not in card_section[1]:
                    card_section[1]['description'] = mark_safe(
                        '<div style="background-color: #fff3cd; border: 1px solid #ffeeba; padding: 10px; border-radius: 5px;">'
                        '<strong>⚠️ Note:</strong> Card has been issued. Card details are auto-generated and cannot be modified manually.'
                        '</div>'
                    )
                fieldsets_list[card_section_index] = tuple(card_section)
        return tuple(fieldsets_list)
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.is_card_issued:
            card_fields = ['cardholder_name', 'card_type', 'is_card_issued']
            for field in card_fields:
                if field not in readonly:
                    readonly.append(field)
        return readonly
    
    def save_model(self, request, obj, form, change):
        if change:
            try:
                old_instance = UserProfile.objects.get(pk=obj.pk)
                if not old_instance.is_card_issued and obj.is_card_issued:
                    from django.utils import timezone
                    from datetime import date
                    from dateutil.relativedelta import relativedelta
                    import random
                    if not obj.card_number:
                        prefix = random.choice(['4', '5'])
                        obj.card_number = prefix + ''.join(str(random.randint(0, 9)) for _ in range(15))
                        obj.card_type = 'Visa' if obj.card_number.startswith('4') else 'Mastercard'
                    if not obj.expiry_date:
                        obj.expiry_date = date.today() + relativedelta(years=3)
                    if not obj.cvv:
                        obj.cvv = str(random.randint(100, 999))
                    obj.card_status = 'active'
                    if not obj.card_application_date:
                        obj.card_application_date = timezone.now()
                    messages.add_message(request, messages.INFO, f'Card details auto-generated for {obj.user.email}')
                if old_instance.is_card_issued and not obj.is_card_issued:
                    obj.card_status = 'blocked'
            except UserProfile.DoesNotExist:
                pass
        obj.save()
    
    actions = ['issue_card_for_selected', 'block_selected_cards', 'activate_selected_cards']
    
    def issue_card_for_selected(self, request, queryset):
        from django.utils import timezone
        from datetime import date
        from dateutil.relativedelta import relativedelta
        import random
        count = 0
        for profile in queryset:
            if not profile.is_card_issued:
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
        count = queryset.filter(is_card_issued=True).update(card_status='blocked')
        self.message_user(request, f'Successfully blocked {count} card(s).')
    block_selected_cards.short_description = 'Block selected cards'
    
    def activate_selected_cards(self, request, queryset):
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
        if obj:
            return ['timestamp']
        return []
