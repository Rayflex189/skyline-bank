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
    # Define loan type choices
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
    
    # Define purpose choices (more specific than loan type)
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
    
    # FIXED: Added default value
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
        # Auto-set requested_date if not provided (backup)
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
    min_profit_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Minimum profit %
    max_profit_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Maximum profit %
    duration_days = models.IntegerField()  # Investment duration in days
    interval_hours = models.IntegerField(null=True, blank=True)  # For short-term investments
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.get_investment_type_display()}"
    
    @property
    def duration_display(self):
        """Display duration in appropriate format"""
        if self.investment_type == 'SHORT_TERM':
            return f"{self.interval_hours} hours" if self.interval_hours else "Short-term"
        else:
            return f"{self.duration_days} days"
    
    @property
    def profit_range_display(self):
        """Display profit range"""
        return f"{self.min_profit_percentage}% - {self.max_profit_percentage}%"

    def get_profit_range(self, amount):
        """Calculate profit range for a given amount"""
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
    
    # Track actual returns if investment is completed
    actual_return = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def calculate_expected_return(self):
        """Calculate expected return based on investment plan"""
        plan = self.investment_plan
        
        # Calculate profit range based on amount invested
        min_profit = self.amount_invested * (plan.min_profit_percentage / 100)
        max_profit = self.amount_invested * (plan.max_profit_percentage / 100)
        
        # Calculate total return (principal + profit)
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
        """Validate that investment amount is within plan limits"""
        plan = self.investment_plan
        
        if self.amount_invested < plan.min_amount:
            return False, f"Minimum investment for this plan is ${plan.min_amount}"
        elif self.amount_invested > plan.max_amount:
            return False, f"Maximum investment for this plan is ${plan.max_amount}"
        
        return True, "Investment amount is valid"

    def get_investment_details(self):
        """Get complete investment details"""
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
            'status': self.get_status_display()
        }

    def save(self, *args, **kwargs):
        # Calculate expected returns if not already set
        if not self.min_expected_return or not self.max_expected_return:
            returns = self.calculate_expected_return()
            self.min_expected_return = returns['min_total']
            self.max_expected_return = returns['max_total']
        
        # Set end date based on plan duration
        if not self.end_date:
            if self.investment_plan.investment_type == 'SHORT_TERM':
                # For short-term, add hours
                self.end_date = timezone.now() + timedelta(hours=self.investment_plan.interval_hours)
            else:
                # For long-term, add days
                self.end_date = timezone.now() + timedelta(days=self.investment_plan.duration_days)
        
        # Auto-complete if past end date
        if self.end_date and timezone.now() > self.end_date and self.status == 'ACTIVE':
            self.status = 'COMPLETED'
            self.completed_at = timezone.now()
            # Set actual return (you can randomize between min and max)
            import random
            min_return = float(self.min_expected_return)
            max_return = float(self.max_expected_return)
            self.actual_return = Decimal(str(random.uniform(min_return, max_return)))
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.investment_plan.name} - ${self.amount_invested} - {self.get_status_display()}"


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


def generate_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_account_number():
    return ''.join(str(random.randint(0, 9)) for _ in range(11))

def generate_otp():
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

def generate_imf():
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

def generate_aml():
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

def generate_vat():
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

def generate_tac():
    return ''.join(str(random.randint(0, 4)) for _ in range(6))

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    balance_after = models.DecimalField(decimal_places=2, max_digits=10)

    # ⬇️ Change this to allow editing
    timestamp = models.DateTimeField(default=timezone.now)  # Editable at creation

    description = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        # Optional: Limit backdating to 1 year
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
    ]
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, blank=True)
    currency_choices = currency_choices = [
        ('$', 'US Dollar'),
        ('€', 'Euro'),
        ('£', 'British Pound'),
        ('¥', 'Japanese Yen'),
        ('A$', 'Australian Dollar'),
        ('C$', 'Canadian Dollar'),
        ('CHF', 'Swiss Franc'),
        ('¥', 'Chinese Yuan'),
        ('kr', 'Swedish Krona'),
        ('$', 'New Zealand Dollar'),
        ('₩', 'South Korean Won'),
        ('$', 'Singapore Dollar'),
        ('kr', 'Norwegian Krone'),
        ('$', 'Mexican Peso'),
        ('₹', 'Indian Rupee'),
        ('₽', 'Russian Ruble'),
        ('R', 'South African Rand'),
        ('R$', 'Brazilian Real'),
        ('₺', 'Turkish Lira'),
        ('$', 'Hong Kong Dollar'),
        ('Rp', 'Indonesian Rupiah'),
        ('RM', 'Malaysian Ringgit'),
        ('₱', 'Philippine Peso'),
        ('฿', 'Thai Baht'),
        ('kr', 'Danish Krone'),
        ('zł', 'Polish Zloty'),
        ('Ft', 'Hungarian Forint'),
        ('Kč', 'Czech Koruna'),
        ('₪', 'Israeli Shekel'),
        ('$', 'Chilean Peso'),
        ('E£', 'Egyptian Pound'),
        ('₴', 'Ukrainian Hryvnia'),
        ('د.إ', 'United Arab Emirates Dirham'),
        ('$', 'Argentine Peso'),
        ('ر.س', 'Saudi Riyal'),
        ('ر.ق', 'Qatari Riyal'),
        ('د.ك', 'Kuwaiti Dinar'),
        ('₦', 'Nigerian Naira'),
        ('৳', 'Bangladeshi Taka'),
        ('₫', 'Vietnamese Dong'),
        ('$', 'Colombian Peso'),
        ('lei', 'Romanian Leu'),
        ('S/', 'Peruvian Sol'),
        ('₨', 'Pakistani Rupee'),
        ('₨', 'Sri Lankan Rupee'),
        ('kn', 'Croatian Kuna'),
        ('лв', 'Bulgarian Lev'),
        ('د.ج', 'Algerian Dinar'),
        ('﷼', 'Iranian Rial'),
        ('$', 'Taiwan Dollar'),
        ('₾', 'Georgian Lari'),
        ('BYN', 'Belarusian Ruble'),
        ('₸', 'Kazakhstani Tenge'),
        ('د.م.', 'Moroccan Dirham'),
        ('Bs', 'Venezuelan Bolívar'),
        ('ብር', 'Ethiopian Birr'),
        ('Sh', 'Ugandan Shilling'),
        ('ج.س.', 'Sudanese Pound'),
        ('₨', 'Nepalese Rupee'),
        ('FCFA', 'Central African CFA Franc'),
        ('CFA', 'West African CFA Franc'),
        ('$', 'East Caribbean Dollar'),
        ('Sh', 'Tanzanian Shilling'),
        ('₵', 'Ghanaian Cedi'),
        ('Sh', 'Kenyan Shilling'),
        ('MT', 'Mozambican Metical'),
        ('Kz', 'Angolan Kwanza'),
        ('Sh', 'Ugandan Shilling'),
        ('د.ت', 'Tunisian Dinar'),
        ('ل.ل', 'Lebanese Pound'),
        ('د.أ', 'Jordanian Dinar'),
        ('Q', 'Guatemalan Quetzal'),
        ('₲', 'Paraguayan Guarani'),
        ('Bs', 'Bolivian Boliviano'),
        ('₣', 'CFP Franc'),
        ('$', 'Bahamian Dollar'),
        ('$', 'Barbadian Dollar'),
        ('$', 'Bermudian Dollar'),
        ('$', 'Fijian Dollar'),
        ('$', 'Guyanese Dollar'),
        ('$', 'Guyanese Dollar'),
        ('L', 'Honduran Lempira'),
        ('J$', 'Jamaican Dollar'),
        ('៛', 'Cambodian Riel'),
        ('с', 'Kyrgyzstani Som'),
        ('₭', 'Lao Kip'),
        ('₨', 'Sri Lankan Rupee'),
        ('Ar', 'Malagasy Ariary'),
        ('lei', 'Moldovan Leu'),
        ('ден', 'Macedonian Denar'),
        ('Ks', 'Myanmar Kyat'),
        ('MOP$', 'Macau Pataca'),
        ('₨', 'Mauritian Rupee'),
        ('Rf', 'Maldivian Rufiyaa'),
        ('MK', 'Malawian Kwacha'),
        ('$', 'Namibian Dollar'),
        ('C$', 'Nicaraguan Córdoba'),
        ('K', 'Papua New Guinean Kina'),
        ('din', 'Serbian Dinar'),
        ('₨', 'Seychellois Rupee'),
        ('£', 'Syrian Pound'),
        ('SM', 'Tajikistani Somoni'),
        ('T$', 'Tongan Paʻanga'),
        ('$', 'Trinidad and Tobago Dollar'),
        ('T', 'Turkmenistan Manat'),
        ('Sh', 'Tanzanian Shilling'),
        ('Sh', 'Ugandan Shilling'),
        ('$', 'Uruguayan Peso'),
        ('лв', 'Uzbekistani Som'),
        ('Vt', 'Vanuatu Vatu'),
        ('T', 'Samoan Tala'),
        ('FCFA', 'Central African CFA Franc'),
        ('SDR', 'Special Drawing Rights'),
        ('CFA', 'West African CFA Franc'),
        ('﷼', 'Yemeni Rial'),
        ('ZK', 'Zambian Kwacha'),
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
    imf_code = models.CharField(max_length=11, default=generate_imf)
    aml_code = models.CharField(max_length=11, default=generate_aml)
    tac_code = models.CharField(max_length=11, default=generate_tac)
    vat_code = models.CharField(max_length=11, default=generate_vat)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_linked = models.BooleanField(default=False)
    is_upgraded = models.BooleanField(default=False)
    last_increment = models.DateTimeField(default=timezone.now)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name']

    def update_savings(self):
        """Increase savings by 10 every 24 hours."""
        now = timezone.now()
        time_diff = now - self.last_increment
        if time_diff >= timedelta(hours=24):
            days_passed = time_diff.days or 1
            self.savings += 10 * days_passed
            self.last_increment = now
            self.save()

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = generate_account_number()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.two_factor_auth == 'enable':
            if not self.four_digit_auth_key or len(self.four_digit_auth_key) != 4:
                raise ValidationError({'four_digit_auth_key': 'A 4-digit authentication key is required when two-factor authentication is enabled.'})
        else:
            # Clear the key if two-factor auth is disabled
            self.four_digit_auth_key = None

    def clean(self):
        # Ensure four_digit_auth_key is a 4-digit integer
        if not self.four_digit_auth_key or not (1000 <= self.four_digit_auth_key <= 9999):
            raise ValidationError("The authentication key must be a 4-digit number.")


    def __str__(self):
        return self.user.email
