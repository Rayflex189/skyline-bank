# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import random
import string
from decimal import Decimal
from cloudinary.models import CloudinaryField

from django.contrib.auth import get_user_model

User = get_user_model()

# ============================================================
# IBAN helper functions
# ============================================================

# Mapping from full country name to ISO 3166-1 alpha-2 code
COUNTRY_CODE_MAP = {
    'United States': 'US',
    'United Kingdom': 'GB',
    'Nigeria': 'NG',
    'Canada': 'CA',
    'Australia': 'AU',
    'Germany': 'DE',
    'France': 'FR',
    'India': 'IN',
    'Italy': 'IT',
    'Spain': 'ES',
    'Brazil': 'BR',
    'Mexico': 'MX',
    'Japan': 'JP',
    'China': 'CN',
    'South Africa': 'ZA',
    'Egypt': 'EG',
    'Kenya': 'KE',
    'Ghana': 'GH',
    'South Korea': 'KR',
    'Singapore': 'SG',
    'Switzerland': 'CH',
    'Sweden': 'SE',
    'Norway': 'NO',
    'Denmark': 'DK',
    'Netherlands': 'NL',
    'Belgium': 'BE',
    'Austria': 'AT',
    'Greece': 'GR',
    'Portugal': 'PT',
    'Ireland': 'IE',
    'New Zealand': 'NZ',
    'Argentina': 'AR',
    'Chile': 'CL',
    'Colombia': 'CO',
    'Peru': 'PE',
    'Venezuela': 'VE',
    'Malaysia': 'MY',
    'Philippines': 'PH',
    'Thailand': 'TH',
    'Vietnam': 'VN',
    'Pakistan': 'PK',
    'Bangladesh': 'BD',
    'Sri Lanka': 'LK',
    'Poland': 'PL',
    'Czech Republic': 'CZ',
    'Romania': 'RO',
    'Hungary': 'HU',
    'Ukraine': 'UA',
    'Russia': 'RU',
    'Turkey': 'TR',
    'Israel': 'IL',
    'Saudi Arabia': 'SA',
    'United Arab Emirates': 'AE',
    'Qatar': 'QA',
    'Kuwait': 'KW',
    'Lebanon': 'LB',
    'Jordan': 'JO',
    'Morocco': 'MA',
    'Tunisia': 'TN',
    'Algeria': 'DZ',
    'Zimbabwe': 'ZW',
    'Zambia': 'ZM',
    'Uganda': 'UG',
    'Tanzania': 'TZ',
    'Sudan': 'SD',
    'South Sudan': 'SS',
    'Ethiopia': 'ET',
    'Somalia': 'SO',
    'Mozambique': 'MZ',
    'Angola': 'AO',
    # add more as needed
}

def generate_iban(country_name):
    """
    Generate a 34-character alphanumeric IBAN-like code.
    Structure: 2-letter country code + 2 check digits + 30 alphanumeric BBAN.
    If country_name is not in the map, defaults to 'XX'.
    """
    country_code = COUNTRY_CODE_MAP.get(country_name, 'XX')
    check_digits = ''.join(random.choices(string.digits, k=2))
    bban = ''.join(random.choices(string.ascii_uppercase + string.digits, k=30))
    return country_code + check_digits + bban

# ============================================================
# Existing helper functions (kept for backward compatibility)
# ============================================================

def generate_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_account_number():
    return ''.join(str(random.randint(0, 9)) for _ in range(11))

def generate_otp():
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

def generate_imf():   # kept for other uses, not used for imf_code anymore
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

def generate_aml():
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

def generate_vat():
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

def generate_tac():
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

def generate_application_fee_code():
    """Generate a unique application fee code for credit card applications."""
    import uuid
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def generate_card_number():
    """Generate a unique 16-digit card number."""
    while True:
        prefix = random.choice(['4', '5'])
        card_number = prefix + ''.join(str(random.randint(0, 9)) for _ in range(15))
        if not UserProfile.objects.filter(card_number=card_number).exists():
            return card_number

def generate_expiry_date():
    from datetime import date
    from dateutil.relativedelta import relativedelta
    return date.today() + relativedelta(years=3)

def generate_cvv():
    return str(random.randint(100, 999))

# ============================================================
# Models
# ============================================================

class KYC(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id_front = models.FileField(upload_to="kyc/")
    id_back = models.FileField(upload_to="kyc/")
    selfie = models.FileField(upload_to="kyc/")
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")],
        default="Pending"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KYC - {self.user.email}"

class Loan(models.Model):
    LOAN_TYPE_CHOICES = [
        ('personal', 'Personal Loan'),
        ('business', 'Business Loan'),
        ('mortgage', 'Mortgage'),
        ('auto', 'Auto Loan'),
        ('education', 'Education Loan'),
        ('medical', 'Medical Loan'),
        ('debt_consolidation', 'Debt Consolidation'),
        ('emergency', 'Emergency Loan'),
        ('home_improvement', 'Home Improvement'),
        ('other', 'Other'),
    ]
    PURPOSE_CHOICES = [
        ('debt_consolidation', 'Debt Consolidation'),
        ('home_improvement', 'Home Improvement'),
        ('medical_expenses', 'Medical Expenses'),
        ('education_fees', 'Education/Tuition Fees'),
        ('business_expansion', 'Business Expansion'),
        ('vehicle_purchase', 'Vehicle Purchase'),
        ('wedding', 'Wedding Expenses'),
        ('travel', 'Travel/Vacation'),
        ('emergency', 'Emergency Funds'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loans'
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(100)]
    )
    loan_type = models.CharField(
        max_length=50,
        choices=LOAN_TYPE_CHOICES,
        default='personal'
    )
    purpose = models.CharField(
        max_length=50,
        choices=PURPOSE_CHOICES,
        default='other'
    )
    repayment_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('biweekly', 'Bi-weekly'),
            ('weekly', 'Weekly'),
        ],
        default='monthly'
    )
    duration = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(360)]
    )
    interest = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    total_payable = models.DecimalField(max_digits=12, decimal_places=2)
    employment_status = models.CharField(
        max_length=30,
        choices=[
            ('employed', 'Employed'),
            ('self_employed', 'Self-Employed'),
            ('unemployed', 'Unemployed'),
            ('student', 'Student'),
            ('retired', 'Retired'),
        ],
        default='employed'
    )
    annual_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    collateral = models.TextField(blank=True, null=True)
    requested_date = models.DateField(default=timezone.now)
    expected_disbursement_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")],
        default="Pending"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Loan - {self.user.email} - ${self.amount} - {self.get_loan_type_display()}"

    def monthly_payment(self):
        if self.duration > 0 and self.interest > 0:
            monthly_rate = (self.interest / 100) / 12
            payment = (monthly_rate * float(self.amount)) / (1 - (1 + monthly_rate) ** -self.duration)
            return round(payment, 2)
        return 0
    
    def save(self, *args, **kwargs):
        if not self.requested_date:
            self.requested_date = timezone.now().date()
        super().save(*args, **kwargs)

class InvestmentPlan(models.Model):
    PLAN_TYPES = [
        ('STARTER', 'Starter Plan'),
        ('PRO', 'Pro Plan'),
        ('ELITE', 'Elite Plan'),
    ]
    INVESTMENT_TYPES = [
        ('SHORT_TERM', 'Short Term Trading'),
        ('LONG_TERM', 'Long Term Investment'),
    ]
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPES, default='SHORT_TERM')
    min_amount = models.DecimalField(max_digits=15, decimal_places=2, default=100.00)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, default=10000.00)
    min_profit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    max_profit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    duration_days = models.IntegerField()
    interval_hours = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.get_investment_type_display()}"
    
    @property
    def duration_display(self):
        if self.investment_type == 'SHORT_TERM':
            return f"{self.interval_hours} hours" if self.interval_hours else "Short-term"
        else:
            return f"{self.duration_days} days"
    
    @property
    def profit_range_display(self):
        return f"{self.min_profit_percentage}% - {self.max_profit_percentage}%"

    def get_profit_range(self, amount):
        min_profit = amount * (self.min_profit_percentage / 100)
        max_profit = amount * (self.max_profit_percentage / 100)
        return {
            'min_profit': min_profit,
            'max_profit': max_profit,
            'profit_range': f"${min_profit:.2f} - ${max_profit:.2f}"
        }

class UserInvestment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    investment_plan = models.ForeignKey('InvestmentPlan', on_delete=models.CASCADE)
    amount_invested = models.DecimalField(max_digits=15, decimal_places=2)
    min_expected_return = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    max_expected_return = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    actual_return = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def progress_percentage(self):
        from django.utils import timezone
        if self.status == 'COMPLETED':
            return 100
        if self.status == 'PENDING':
            return 0
        try:
            total_days = (self.end_date - self.start_date).days
            if total_days <= 0:
                return 100
            today = timezone.now()
            days_passed = (today - self.start_date).days
            if days_passed < 0:
                return 0
            elif days_passed > total_days:
                return 100
            return min(100, max(0, round((days_passed / total_days) * 100, 1)))
        except (TypeError, AttributeError):
            return 0
    
    @property
    def days_remaining(self):
        from django.utils import timezone
        if self.status in ['COMPLETED', 'CANCELLED']:
            return 0
        today = timezone.now()
        if self.end_date > today:
            remaining = (self.end_date - today).days
            return max(0, remaining)
        return 0
    
    @property
    def days_passed(self):
        from django.utils import timezone
        if self.status == 'PENDING':
            return 0
        today = timezone.now()
        if today > self.start_date:
            return max(0, (today - self.start_date).days)
        return 0
    
    @property
    def total_days(self):
        try:
            return (self.end_date - self.start_date).days
        except (TypeError, AttributeError):
            return 0
    
    @property
    def current_value(self):
        if self.status == 'COMPLETED':
            if self.actual_return:
                return self.actual_return
            return self.max_expected_return or self.amount_invested
        if self.status == 'ACTIVE':
            progress = self.progress_percentage / 100
            min_return = self.min_expected_return or self.amount_invested
            max_return = self.max_expected_return or self.amount_invested
            min_profit = float(min_return) - float(self.amount_invested)
            max_profit = float(max_return) - float(self.amount_invested)
            current_min_profit = min_profit * progress
            current_max_profit = max_profit * progress
            current_profit = (current_min_profit + current_max_profit) / 2
            current_value = float(self.amount_invested) + current_profit
            return Decimal(str(round(current_value, 2)))
        return self.amount_invested
    
    @property
    def current_profit(self):
        current_val = float(self.current_value)
        invested = float(self.amount_invested)
        return Decimal(str(round(current_val - invested, 2)))
    
    @property
    def roi_percentage(self):
        invested = float(self.amount_invested)
        if invested > 0:
            profit = float(self.current_profit)
            return Decimal(str(round((profit / invested) * 100, 2)))
        return Decimal('0')
    
    @property
    def profit_range_display(self):
        if self.investment_plan:
            return f"{self.investment_plan.min_profit_percentage}% - {self.investment_plan.max_profit_percentage}%"
        return "N/A"
    
    @property
    def expected_return_range(self):
        min_return = self.min_expected_return or self.amount_invested
        max_return = self.max_expected_return or self.amount_invested
        return f"${float(min_return):,.2f} - ${float(max_return):,.2f}"

    def calculate_expected_return(self):
        plan = self.investment_plan
        min_profit = self.amount_invested * (plan.min_profit_percentage / 100)
        max_profit = self.amount_invested * (plan.max_profit_percentage / 100)
        min_total = self.amount_invested + min_profit
        max_total = self.amount_invested + max_profit
        return {
            'min_profit': min_profit,
            'max_profit': max_profit,
            'min_total': min_total,
            'max_total': max_total,
            'profit_percentage_range': f"{plan.min_profit_percentage}% - {plan.max_profit_percentage}%",
            'profit_range': f"${min_profit:.2f} - ${max_profit:.2f}",
            'total_range': f"${min_total:.2f} - ${max_total:.2f}"
        }

    def validate_investment_amount(self):
        plan = self.investment_plan
        if self.amount_invested < plan.min_amount:
            return False, f"Minimum investment for this plan is ${plan.min_amount}"
        elif self.amount_invested > plan.max_amount:
            return False, f"Maximum investment for this plan is ${plan.max_amount}"
        return True, "Investment amount is valid"

    def get_investment_details(self):
        is_valid, message = self.validate_investment_amount()
        if not is_valid:
            return {
                'valid': False,
                'message': message,
                'amount_invested': self.amount_invested,
                'plan_name': self.investment_plan.name,
                'investment_type': self.investment_plan.get_investment_type_display()
            }
        returns = self.calculate_expected_return()
        return {
            'valid': True,
            'plan_name': self.investment_plan.name,
            'investment_type': self.investment_plan.get_investment_type_display(),
            'amount_invested': self.amount_invested,
            'min_profit': returns['min_profit'],
            'max_profit': returns['max_profit'],
            'min_total_return': returns['min_total'],
            'max_total_return': returns['max_total'],
            'profit_percentage_range': returns['profit_percentage_range'],
            'profit_range': returns['profit_range'],
            'total_range': returns['total_range'],
            'duration': self.investment_plan.duration_display,
            'interval': f"{self.investment_plan.interval_hours} hours" if self.investment_plan.interval_hours else "N/A",
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.get_status_display(),
            'progress_percentage': self.progress_percentage,
            'days_remaining': self.days_remaining,
            'current_value': self.current_value,
            'current_profit': self.current_profit,
            'roi_percentage': self.roi_percentage,
        }

    def save(self, *args, **kwargs):
        if not self.min_expected_return or not self.max_expected_return:
            returns = self.calculate_expected_return()
            self.min_expected_return = returns['min_total']
            self.max_expected_return = returns['max_total']
        if not self.end_date:
            if self.investment_plan.investment_type == 'SHORT_TERM' and self.investment_plan.interval_hours:
                self.end_date = timezone.now() + timedelta(hours=self.investment_plan.interval_hours)
            else:
                self.end_date = timezone.now() + timedelta(days=self.investment_plan.duration_days)
        if self.end_date and timezone.now() > self.end_date and self.status == 'ACTIVE':
            self.status = 'COMPLETED'
            self.completed_at = timezone.now()
            if self.min_expected_return and self.max_expected_return:
                min_return = float(self.min_expected_return)
                max_return = float(self.max_expected_return)
                self.actual_return = Decimal(str(round(random.uniform(min_return, max_return), 2)))
            else:
                self.actual_return = self.amount_invested
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.investment_plan.name} - ${self.amount_invested} - {self.get_status_display()}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Investment"
        verbose_name_plural = "User Investments"

class InvestmentTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('INVESTMENT', 'Investment'),
        ('RETURN', 'Return'),
        ('BONUS', 'Bonus'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    investment = models.ForeignKey(UserInvestment, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ${self.amount}"

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    balance_after = models.DecimalField(decimal_places=2, max_digits=10)
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        one_year_ago = timezone.now() - timedelta(days=365)
        if self.timestamp < one_year_ago:
            raise ValidationError("You can only backdate transactions up to 1 year.")

    def __str__(self):
        return f"{self.amount} - {self.user.email} - {self.timestamp}"

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    OCCUPATION_CHOICES = [
        ('management', 'Management'),
        ('business_finance', 'Business and Financial Operations'),
        ('computer_math', 'Computer and Mathematical'),
        ('architecture_engineering', 'Architecture and Engineering'),
        ('life_sciences', 'Life, Physical, and Social Sciences'),
        ('community_social', 'Community and Social Service'),
        ('legal', 'Legal'),
        ('education', 'Education, Training, and Library'),
        ('arts_design', 'Arts, Design, Entertainment, Sports, and Media'),
        ('healthcare', 'Healthcare Practitioners and Technical'),
    ]
    occupation = models.CharField(max_length=50, default='select your occupation', choices=OCCUPATION_CHOICES, blank=True, null=True)
    next_of_kin = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(unique=True, max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    TWO_FACTOR_AUTH_CHOICES = [
        ('enable', 'Enable'),
        ('disable', 'Disable'),
    ]
    two_factor_auth = models.CharField(
        max_length=10,
        choices=TWO_FACTOR_AUTH_CHOICES,
        default='disable'
    )
    four_digit_auth_key = models.IntegerField(blank=True, null=True)
    address = models.TextField(max_length=255, blank=True, null=True)
    zip_code = models.IntegerField(blank=True, null=True)
    COUNTRY_CHOICES = [
        ('Afghanistan', 'Afghanistan'),
        ('Albania', 'Albania'),
        ('Algeria', 'Algeria'),
        ('Andorra', 'Andorra'),
        ('Angola', 'Angola'),
        ('Anguilla', 'Anguilla'),
        ('Antigua and Barbuda', 'Antigua and Barbuda'),
        ('Argentina', 'Argentina'),
        ('Armenia', 'Armenia'),
        ('Aruba', 'Aruba'),
        ('Australia', 'Australia'),
        ('Austria', 'Austria'),
        ('Azerbaijan', 'Azerbaijan'),
        ('Bahamas', 'Bahamas'),
        ('Bahrain', 'Bahrain'),
        ('Bangladesh', 'Bangladesh'),
        ('Barbados', 'Barbados'),
        ('Belarus', 'Belarus'),
        ('Belgium', 'Belgium'),
        ('Belize', 'Belize'),
        ('Benin', 'Benin'),
        ('Bermuda', 'Bermuda'),
        ('Bhutan', 'Bhutan'),
        ('Bolivia', 'Bolivia'),
        ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'),
        ('Botswana', 'Botswana'),
        ('Brazil', 'Brazil'),
        ('British Virgin Islands', 'British Virgin Islands'),
        ('Brunei', 'Brunei'),
        ('Bulgaria', 'Bulgaria'),
        ('Burkina Faso', 'Burkina Faso'),
        ('Burundi', 'Burundi'),
        ('Cambodia', 'Cambodia'),
        ('Cameroon', 'Cameroon'),
        ('Canada', 'Canada'),
        ('Cape Verde', 'Cape Verde'),
        ('Cayman Islands', 'Cayman Islands'),
        ('Central African Republic', 'Central African Republic'),
        ('Chad', 'Chad'),
        ('Chile', 'Chile'),
        ('China', 'China'),
        ('Colombia', 'Colombia'),
        ('Comoros', 'Comoros'),
        ('Congo', 'Congo'),
        ('Cook Islands', 'Cook Islands'),
        ('Costa Rica', 'Costa Rica'),
        ('Croatia', 'Croatia'),
        ('Cuba', 'Cuba'),
        ('Cyprus', 'Cyprus'),
        ('Czech Republic', 'Czech Republic'),
        ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'),
        ('Denmark', 'Denmark'),
        ('Djibouti', 'Djibouti'),
        ('Dominica', 'Dominica'),
        ('Dominican Republic', 'Dominican Republic'),
        ('East Timor', 'East Timor'),
        ('Ecuador', 'Ecuador'),
        ('Egypt', 'Egypt'),
        ('El Salvador', 'El Salvador'),
        ('Equatorial Guinea', 'Equatorial Guinea'),
        ('Eritrea', 'Eritrea'),
        ('Estonia', 'Estonia'),
        ('Ethiopia', 'Ethiopia'),
        ('Faroe Islands', 'Faroe Islands'),
        ('Fiji', 'Fiji'),
        ('Finland', 'Finland'),
        ('France', 'France'),
        ('French Guiana', 'French Guiana'),
        ('French Polynesia', 'French Polynesia'),
        ('Gabon', 'Gabon'),
        ('Gambia', 'Gambia'),
        ('Georgia', 'Georgia'),
        ('Germany', 'Germany'),
        ('Ghana', 'Ghana'),
        ('Gibraltar', 'Gibraltar'),
        ('Greece', 'Greece'),
        ('Greenland', 'Greenland'),
        ('Grenada', 'Grenada'),
        ('Guadeloupe', 'Guadeloupe'),
        ('Guatemala', 'Guatemala'),
        ('Guinea', 'Guinea'),
        ('Guinea-Bissau', 'Guinea-Bissau'),
        ('Guyana', 'Guyana'),
        ('Haiti', 'Haiti'),
        ('Honduras', 'Honduras'),
        ('Hong Kong', 'Hong Kong'),
        ('Hungary', 'Hungary'),
        ('Iceland', 'Iceland'),
        ('India', 'India'),
        ('Indonesia', 'Indonesia'),
        ('Iran', 'Iran'),
        ('Iraq', 'Iraq'),
        ('Ireland', 'Ireland'),
        ('Israel', 'Israel'),
        ('Italy', 'Italy'),
        ('Ivory Coast', 'Ivory Coast'),
        ('Jamaica', 'Jamaica'),
        ('Japan', 'Japan'),
        ('Jordan', 'Jordan'),
        ('Kazakhstan', 'Kazakhstan'),
        ('Kenya', 'Kenya'),
        ('Kiribati', 'Kiribati'),
        ('Kuwait', 'Kuwait'),
        ('Kyrgyzstan', 'Kyrgyzstan'),
        ('Laos', 'Laos'),
        ('Latvia', 'Latvia'),
        ('Lebanon', 'Lebanon'),
        ('Lesotho', 'Lesotho'),
        ('Liberia', 'Liberia'),
        ('Libya', 'Libya'),
        ('Liechtenstein', 'Liechtenstein'),
        ('Lithuania', 'Lithuania'),
        ('Luxembourg', 'Luxembourg'),
        ('Macau', 'Macau'),
        ('Macedonia', 'Macedonia'),
        ('Madagascar', 'Madagascar'),
        ('Malawi', 'Malawi'),
        ('Malaysia', 'Malaysia'),
        ('Maldives', 'Maldives'),
        ('Mali', 'Mali'),
        ('Malta', 'Malta'),
        ('Marshall Islands', 'Marshall Islands'),
        ('Martinique', 'Martinique'),
        ('Mauritania', 'Mauritania'),
        ('Mauritius', 'Mauritius'),
        ('Mayotte', 'Mayotte'),
        ('Mexico', 'Mexico'),
        ('Micronesia', 'Micronesia'),
        ('Moldova', 'Moldova'),
        ('Monaco', 'Monaco'),
        ('Mongolia', 'Mongolia'),
        ('Montenegro', 'Montenegro'),
        ('Montserrat', 'Montserrat'),
        ('Morocco', 'Morocco'),
        ('Mozambique', 'Mozambique'),
        ('Myanmar', 'Myanmar'),
        ('Namibia', 'Namibia'),
        ('Nauru', 'Nauru'),
        ('Nepal', 'Nepal'),
        ('Netherlands', 'Netherlands'),
        ('New Caledonia', 'New Caledonia'),
        ('New Zealand', 'New Zealand'),
        ('Nicaragua', 'Nicaragua'),
        ('Niger', 'Niger'),
        ('Nigeria', 'Nigeria'),
        ('Niue', 'Niue'),
        ('Norfolk Island', 'Norfolk Island'),
        ('North Korea', 'North Korea'),
        ('Norway', 'Norway'),
        ('Oman', 'Oman'),
        ('Pakistan', 'Pakistan'),
        ('Palau', 'Palau'),
        ('Palestinian Territory', 'Palestinian Territory'),
        ('Panama', 'Panama'),
        ('Papua New Guinea', 'Papua New Guinea'),
        ('Paraguay', 'Paraguay'),
        ('Peru', 'Peru'),
        ('Philippines', 'Philippines'),
        ('Poland', 'Poland'),
        ('Portugal', 'Portugal'),
        ('Qatar', 'Qatar'),
        ('Reunion', 'Reunion'),
        ('Romania', 'Romania'),
        ('Russia', 'Russia'),
        ('Rwanda', 'Rwanda'),
        ('Saint Barthelemy', 'Saint Barthelemy'),
        ('Saint Helena', 'Saint Helena'),
        ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'),
        ('Saint Lucia', 'Saint Lucia'),
        ('Saint Martin', 'Saint Martin'),
        ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'),
        ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'),
        ('Samoa', 'Samoa'),
        ('San Marino', 'San Marino'),
        ('Sao Tome and Principe', 'Sao Tome and Principe'),
        ('Saudi Arabia', 'Saudi Arabia'),
        ('Senegal', 'Senegal'),
        ('Serbia', 'Serbia'),
        ('Seychelles', 'Seychelles'),
        ('Sierra Leone', 'Sierra Leone'),
        ('Singapore', 'Singapore'),
        ('Slovakia', 'Slovakia'),
        ('Slovenia', 'Slovenia'),
        ('Solomon Islands', 'Solomon Islands'),
        ('Somalia', 'Somalia'),
        ('South Africa', 'South Africa'),
        ('South Korea', 'South Korea'),
        ('South Sudan', 'South Sudan'),
        ('Spain', 'Spain'),
        ('Sri Lanka', 'Sri Lanka'),
        ('Sudan', 'Sudan'),
        ('Suriname', 'Suriname'),
        ('Swaziland', 'Swaziland'),
        ('Sweden', 'Sweden'),
        ('Switzerland', 'Switzerland'),
        ('Syria', 'Syria'),
        ('Taiwan', 'Taiwan'),
        ('Tajikistan', 'Tajikistan'),
        ('Tanzania', 'Tanzania'),
        ('Thailand', 'Thailand'),
        ('Togo', 'Togo'),
        ('Tonga', 'Tonga'),
        ('Trinidad and Tobago', 'Trinidad and Tobago'),
        ('Tunisia', 'Tunisia'),
        ('Turkey', 'Turkey'),
        ('Turkmenistan', 'Turkmenistan'),
        ('Turks and Caicos Islands', 'Turks and Caicos Islands'),
        ('Tuvalu', 'Tuvalu'),
        ('Uganda', 'Uganda'),
        ('Ukraine', 'Ukraine'),
        ('United Arab Emirates', 'United Arab Emirates'),
        ('United Kingdom', 'United Kingdom'),
        ('United States', 'United States'),
        ('Uruguay', 'Uruguay'),
        ('Uzbekistan', 'Uzbekistan'),
        ('Vanuatu', 'Vanuatu'),
        ('Vatican City', 'Vatican City'),
        ('Venezuela', 'Venezuela'),
        ('Vietnam', 'Vietnam'),
        ('Yemen', 'Yemen'),
        ('Zambia', 'Zambia'),
        ('Zimbabwe', 'Zimbabwe'),
        ('Western Sahara', 'Western Sahara'),
        ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'),
    ]
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, blank=True)
    currency_choices = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
        ('AUD', 'Australian Dollar'),
        ('CAD', 'Canadian Dollar'),
        ('CHF', 'Swiss Franc'),
        ('CNY', 'Chinese Yuan'),
        ('SEK', 'Swedish Krona'),
        ('NZD', 'New Zealand Dollar'),
        ('KRW', 'South Korean Won'),
        ('SGD', 'Singapore Dollar'),
        ('NOK', 'Norwegian Krone'),
        ('MXN', 'Mexican Peso'),
        ('INR', 'Indian Rupee'),
        ('RUB', 'Russian Ruble'),
        ('ZAR', 'South African Rand'),
        ('BRL', 'Brazilian Real'),
        ('TRY', 'Turkish Lira'),
        ('HKD', 'Hong Kong Dollar'),
        ('IDR', 'Indonesian Rupiah'),
        ('MYR', 'Malaysian Ringgit'),
        ('PHP', 'Philippine Peso'),
        ('THB', 'Thai Baht'),
        ('DKK', 'Danish Krone'),
        ('PLN', 'Polish Zloty'),
        ('HUF', 'Hungarian Forint'),
        ('CZK', 'Czech Koruna'),
        ('ILS', 'Israeli Shekel'),
        ('CLP', 'Chilean Peso'),
        ('EGP', 'Egyptian Pound'),
        ('UAH', 'Ukrainian Hryvnia'),
        ('AED', 'United Arab Emirates Dirham'),
        ('ARS', 'Argentine Peso'),
        ('SAR', 'Saudi Riyal'),
        ('QAR', 'Qatari Riyal'),
        ('KWD', 'Kuwaiti Dinar'),
        ('NGN', 'Nigerian Naira'),
        ('BDT', 'Bangladeshi Taka'),
        ('VND', 'Vietnamese Dong'),
        ('COP', 'Colombian Peso'),
        ('RON', 'Romanian Leu'),
        ('PEN', 'Peruvian Sol'),
        ('PKR', 'Pakistani Rupee'),
        ('LKR', 'Sri Lankan Rupee'),
        ('HRK', 'Croatian Kuna'),
        ('BGN', 'Bulgarian Lev'),
        ('DZD', 'Algerian Dinar'),
        ('IRR', 'Iranian Rial'),
        ('TWD', 'Taiwan Dollar'),
        ('GEL', 'Georgian Lari'),
        ('BYN', 'Belarusian Ruble'),
        ('KZT', 'Kazakhstani Tenge'),
        ('MAD', 'Moroccan Dirham'),
        ('VES', 'Venezuelan Bolívar'),
        ('ETB', 'Ethiopian Birr'),
        ('UGX', 'Ugandan Shilling'),
        ('SDG', 'Sudanese Pound'),
        ('NPR', 'Nepalese Rupee'),
        ('XAF', 'Central African CFA Franc'),
        ('XOF', 'West African CFA Franc'),
        ('XCD', 'East Caribbean Dollar'),
        ('TZS', 'Tanzanian Shilling'),
        ('GHS', 'Ghanaian Cedi'),
        ('KES', 'Kenyan Shilling'),
        ('MZN', 'Mozambican Metical'),
        ('AOA', 'Angolan Kwanza'),
        ('TND', 'Tunisian Dinar'),
        ('LBP', 'Lebanese Pound'),
        ('JOD', 'Jordanian Dinar'),
        ('GTQ', 'Guatemalan Quetzal'),
        ('PYG', 'Paraguayan Guarani'),
        ('BOB', 'Bolivian Boliviano'),
        ('XPF', 'CFP Franc'),
        ('BSD', 'Bahamian Dollar'),
        ('BBD', 'Barbadian Dollar'),
        ('BMD', 'Bermudian Dollar'),
        ('FJD', 'Fijian Dollar'),
        ('GYD', 'Guyanese Dollar'),
        ('HNL', 'Honduran Lempira'),
        ('JMD', 'Jamaican Dollar'),
        ('KHR', 'Cambodian Riel'),
        ('KGS', 'Kyrgyzstani Som'),
        ('LAK', 'Lao Kip'),
        ('LKR', 'Sri Lankan Rupee'),
        ('MGA', 'Malagasy Ariary'),
        ('MDL', 'Moldovan Leu'),
        ('MKD', 'Macedonian Denar'),
        ('MMK', 'Myanmar Kyat'),
        ('MOP', 'Macau Pataca'),
        ('MUR', 'Mauritian Rupee'),
        ('MVR', 'Maldivian Rufiyaa'),
        ('MWK', 'Malawian Kwacha'),
        ('NAD', 'Namibian Dollar'),
        ('NIO', 'Nicaraguan Córdoba'),
        ('PGK', 'Papua New Guinean Kina'),
        ('RSD', 'Serbian Dinar'),
        ('SCR', 'Seychellois Rupee'),
        ('SYP', 'Syrian Pound'),
        ('TJS', 'Tajikistani Somoni'),
        ('TOP', 'Tongan Paʻanga'),
        ('TTD', 'Trinidad and Tobago Dollar'),
        ('TMT', 'Turkmenistan Manat'),
        ('UYU', 'Uruguayan Peso'),
        ('UZS', 'Uzbekistani Som'),
        ('VUV', 'Vanuatu Vatu'),
        ('WST', 'Samoan Tala'),
        ('XDR', 'Special Drawing Rights'),
        ('YER', 'Yemeni Rial'),
        ('ZMW', 'Zambian Kwacha'),
    ]
    currency = models.CharField(max_length=4, choices=currency_choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    working_choices = [
        ('Employed', 'Employed'),
        ('Unemployed', 'Unemployed'),
        ('Retired', 'Retired'),
        ('Student', 'Student'),
        ('Others', 'Others'),
    ]
    status = models.CharField(max_length=50, choices=working_choices, blank=True)
    gender_choices = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    Gender = models.CharField(max_length=50, choices=gender_choices, blank=True)
    account_choices = [
        ('Online Account', 'Online Account'),
        ('Checking Account', 'Checking Account'),
        ('Current Account', 'Current Account'),
        ('Corporate Account', 'Corporate Account'),
        ('Offshore Account', 'Offshore Account'),
        ('Joint Account', 'Joint Account'),
    ]
    account_type = models.CharField(max_length=50, choices=account_choices, blank=True)
    profile_pic = CloudinaryField('profile_pic', null=True, blank=True)
    account_number = models.CharField(max_length=11, default=generate_account_number)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), null=True)
    savings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=True, null=True)
    linking_code = models.CharField(max_length=11, default=generate_code)
    otp_code = models.CharField(max_length=11, default=generate_otp)
    
    # CHANGED: imf_code now stores a 34-character IBAN-like code
    imf_code = models.CharField(max_length=34, blank=True, null=True)   # was max_length=11, default=generate_imf
    
    aml_code = models.CharField(max_length=11, default=generate_aml)
    tac_code = models.CharField(max_length=11, default=generate_tac)
    vat_code = models.CharField(max_length=11, default=generate_vat)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_linked = models.BooleanField(default=False)
    is_upgraded = models.BooleanField(default=False)
    last_increment = models.DateTimeField(default=timezone.now)
    is_email_verified = models.BooleanField(default=False)

    # Card fields
    cardholder_name = models.CharField(max_length=100, blank=True, null=True)
    card_number = models.CharField(max_length=16, unique=True, blank=True, null=True)
    card_type = models.CharField(max_length=20, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    cvv = models.CharField(max_length=4, blank=True, null=True)
    card_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('blocked', 'Blocked'),
            ('expired', 'Expired'),
        ],
        default='pending'
    )
    application_fee_code = models.CharField(
        max_length=11, 
        unique=True, 
        blank=True, 
        null=True
    )
    card_application_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_card_issued = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store original country to detect changes
        self._original_country = self.country

    def update_savings(self):
        now = timezone.now()
        time_diff = now - self.last_increment
        if time_diff >= timedelta(hours=24):
            days_passed = time_diff.days or 1
            self.savings += 10 * days_passed
            self.last_increment = now
            self.save()

    def save(self, *args, **kwargs):
        # Generate account number if not present
        if not self.account_number:
            self.account_number = generate_account_number()
        
        # Auto-generate application fee code on account creation
        if not self.application_fee_code:
            self.application_fee_code = generate_application_fee_code()
        
        # Generate IBAN-like code if empty or country changed
        if not self.imf_code or (self.country and self.country != self._original_country):
            if self.country:
                self.imf_code = generate_iban(self.country)
            else:
                # fallback if country not set
                self.imf_code = generate_iban('XX')
        
        # Auto-generate card details when card is issued
        if self.is_card_issued and not self.card_number:
            self.card_number = generate_card_number()
            self.expiry_date = generate_expiry_date()
            self.cvv = generate_cvv()
            if self.card_number.startswith('4'):
                self.card_type = 'Visa'
            elif self.card_number.startswith('5'):
                self.card_type = 'Mastercard'
            else:
                self.card_type = 'Visa'
            self.card_status = 'active'
        
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.two_factor_auth == "enable":
            if not self.four_digit_auth_key or not (1000 <= self.four_digit_auth_key <= 9999):
                raise ValidationError({
                    "four_digit_auth_key": "Authentication key must be a 4-digit number."
                })
        else:
            self.four_digit_auth_key = None

    def __str__(self):
        return self.user.email
