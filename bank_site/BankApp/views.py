# Django Core Imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from django.urls import reverse

# Utility Imports
from datetime import timedelta, datetime
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout

# Project Imports
from .decorators import *
from .forms import *
from .models import *
from .utilis import *  # If still required (consider limiting *)
from BankApp.decorators import unauthenticated_user
from BankApp.models import UserProfile


User = get_user_model()
signer = TimestampSigner()

from django.contrib.admin.views.decorators import staff_member_required

from django.http import HttpResponse
from docx import Document

def submit_loan(request):
    if request.method == "POST":
        form = LoanForm(request.POST)

        if form.is_valid():
            loan = form.save(commit=False)
            loan.user = request.user

            # calculate interest
            rate, total = calculate_interest(loan.loan_amount, loan.loan_duration)
            loan.interest_rate = rate
            loan.total_amount_due = total

            loan.save()

            # generate PDF
            pdf_path = generate_loan_pdf(loan)

            # email PDF
            email_pdf(request.user.email, pdf_path)

            messages.success(request, "Loan submitted successfully! Approval sent to email.")
            return redirect("dashboard")
    else:
        form = LoanForm()

    return render(request, "BankApp/submit_loans.html", {"form": form})


def send_kyc_email(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Attach the user's latest KYC if you want
    try:
        kyc = KYC.objects.get(user=user)
    except KYC.DoesNotExist:
        kyc = None

    subject = "Your KYC Verification Status"
    message = (
        f"Dear {user.first_name},\n\n"
        "Thank you for submitting your KYC details. "
        "Your verification is being reviewed.\n\n"
        "Best regards,\nYour Bank Team"
    )

    email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [user.email])
    email.send()

    messages.success(request, "KYC email sent successfully.")
    return redirect("dashboard")  # or anywhere you want



def download_kyc_pdf(request, user_id):
    user_profile = get_object_or_404(UserProfile, user_id=user_id)

    # Create a DOCX file
    doc = Document()
    doc.add_heading("KYC Details", level=1)

    doc.add_paragraph(f"Full Name: {user_profile.full_name}")
    doc.add_paragraph(f"Email: {user_profile.user.email}")
    doc.add_paragraph(f"Phone: {user_profile.phone}")
    doc.add_paragraph(f"Address: {user_profile.address}")
    doc.add_paragraph(f"Occupation: {user_profile.occupation}")
    doc.add_paragraph(f"City: {user_profile.city}")
    doc.add_paragraph(f"ZIP Code: {user_profile.zip_code}")

    # Save to buffer
    file_name = f"KYC_{user_profile.user.email}.docx"
    file_path = f"/tmp/{file_name}"
    doc.save(file_path)

    with open(file_path, "rb") as file:
        response = HttpResponse(file.read(), content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Loan, UserProfile
from django.contrib.auth.models import User
from django.db.models import Count, Q
import datetime

@staff_member_required
def manage_loans(request):
    """
    Main loan management view for staff members.
    Includes filtering, search, and statistics.
    """
    # Get all loans ordered by creation date
    loans = Loan.objects.all().order_by('-created_at')
    
    # Get filter parameters from GET request
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    # Apply filters
    if status_filter:
        loans = loans.filter(status__iexact=status_filter)
    
    if search_query:
        loans = loans.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(loan_purpose__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Get statistics for the dashboard
    total_loans = Loan.objects.count()
    pending_loans = Loan.objects.filter(status__iexact='pending').count()
    approved_loans = Loan.objects.filter(status__iexact='approved').count()
    rejected_loans = Loan.objects.filter(status__iexact='rejected').count()
    
    # Calculate processing fees (5% of loan amount)
    for loan in loans:
        if not hasattr(loan, 'processing_fee') or loan.processing_fee is None:
            loan.processing_fee = loan.loan_amount * 0.05
    
    # Handle bulk actions
    if request.method == 'POST' and 'action' in request.POST:
        loan_ids = request.POST.getlist('loan_ids')
        action = request.POST.get('action')
        
        if loan_ids and action:
            loans_to_process = Loan.objects.filter(id__in=loan_ids)
            
            if action == 'approve':
                loans_to_process.update(status='approved')
                messages.success(request, f'{len(loan_ids)} loan(s) approved successfully.')
            elif action == 'reject':
                loans_to_process.update(status='rejected')
                messages.success(request, f'{len(loan_ids)} loan(s) rejected.')
            
            return redirect('manage_loans')
    
    context = {
        'loans': loans,
        'total_count': total_loans,
        'pending_count': pending_loans,
        'approved_count': approved_loans,
        'rejected_count': rejected_loans,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': ['pending', 'approved', 'rejected'],
    }
    
    return render(request, 'BankApp/manage_loans.html', context)


@staff_member_required
def approve_loan(request, loan_id):
    """
    Approve individual loan and send notification email.
    """
    try:
        loan = get_object_or_404(Loan, id=loan_id)
        
        # Check if already approved
        if loan.status == 'approved':
            messages.warning(request, f"Loan #{loan.id} is already approved.")
            return redirect('manage_loans')
        
        # Update status
        loan.status = 'approved'
        loan.save()
        
        # Calculate total amount due (loan amount + 5% processing fee)
        processing_fee = loan.loan_amount * 0.05
        total_due = loan.loan_amount + processing_fee
        
        # Send approval email
        try:
            send_mail(
                subject="Loan Approved - SkyBridge Finance",
                message=(
                    f"Hello {loan.full_name},\n\n"
                    f"Congratulations! Your loan application (ID: #{loan.id}) has been approved.\n\n"
                    f"Loan Details:\n"
                    f"Amount: ${loan.loan_amount:,.2f}\n"
                    f"Processing Fee (5%): ${processing_fee:,.2f}\n"
                    f"Total Amount Due: ${total_due:,.2f}\n"
                    f"Purpose: {loan.loan_purpose}\n\n"
                    f"Next Steps:\n"
                    f"1. Please login to your account\n"
                    f"2. Review the loan terms\n"
                    f"3. Accept the loan agreement\n\n"
                    f"You will receive the funds within 2-3 business days.\n\n"
                    "If you have any questions, please contact our support team.\n\n"
                    "Best regards,\n"
                    "SkyBridge Finance Team\n"
                    "support@skybridgefinance.online"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[loan.email],
                fail_silently=False,
            )
            email_sent = True
        except Exception as e:
            email_sent = False
            messages.warning(request, f"Loan approved but email failed to send: {str(e)}")
        
        # Success message
        if email_sent:
            messages.success(request, f"Loan #{loan.id} approved and notification email sent.")
        else:
            messages.success(request, f"Loan #{loan.id} approved (email notification failed).")
            
    except Loan.DoesNotExist:
        messages.error(request, "Loan not found.")
    except Exception as e:
        messages.error(request, f"Error approving loan: {str(e)}")
    
    return redirect('manage_loans')


@staff_member_required
def reject_loan(request, loan_id):
    """
    Reject individual loan and send notification email.
    """
    try:
        loan = get_object_or_404(Loan, id=loan_id)
        
        # Check if already rejected
        if loan.status == 'rejected':
            messages.warning(request, f"Loan #{loan.id} is already rejected.")
            return redirect('manage_loans')
        
        # Update status
        loan.status = 'rejected'
        loan.save()
        
        # Get rejection reason from form if available
        rejection_reason = request.POST.get('rejection_reason', 
                                          "Your application did not meet our current lending criteria.")
        
        # Send rejection email
        try:
            send_mail(
                subject="Loan Application Update - SkyBridge Finance",
                message=(
                    f"Hello {loan.full_name},\n\n"
                    f"We regret to inform you that your loan application (ID: #{loan.id}) "
                    f"for ${loan.loan_amount:,.2f} has not been approved at this time.\n\n"
                    f"Reason: {rejection_reason}\n\n"
                    f"You may reapply in 30 days or contact our support team for more information.\n\n"
                    f"Application Details:\n"
                    f"Amount Requested: ${loan.loan_amount:,.2f}\n"
                    f"Purpose: {loan.loan_purpose}\n\n"
                    f"Thank you for considering SkyBridge Finance for your lending needs.\n\n"
                    "Best regards,\n"
                    "SkyBridge Finance Team\n"
                    "support@skybridgefinance.online"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[loan.email],
                fail_silently=False,
            )
            email_sent = True
        except Exception as e:
            email_sent = False
            messages.warning(request, f"Loan rejected but email failed to send: {str(e)}")
        
        # Success message
        if email_sent:
            messages.error(request, f"Loan #{loan.id} rejected and notification email sent.")
        else:
            messages.error(request, f"Loan #{loan.id} rejected (email notification failed).")
            
    except Loan.DoesNotExist:
        messages.error(request, "Loan not found.")
    except Exception as e:
        messages.error(request, f"Error rejecting loan: {str(e)}")
    
    return redirect('manage_loans')


@staff_member_required
def view_loan_details(request, loan_id):
    """
    View detailed information about a specific loan.
    """
    loan = get_object_or_404(Loan, id=loan_id)
    
    # Calculate additional information
    processing_fee = loan.loan_amount * 0.05
    total_due = loan.loan_amount + processing_fee
    
    context = {
        'loan': loan,
        'processing_fee': processing_fee,
        'total_due': total_due,
    }
    
    return render(request, 'BankApp/loan_details.html', context)


@staff_member_required
def admin_dashboard(request):
    """
    Admin dashboard with overview statistics.
    """
    total_users = UserProfile.objects.count()
    total_loans = Loan.objects.count()
    approved_loans = Loan.objects.filter(status='approved').count()
    pending_loans = Loan.objects.filter(status='pending').count()
    rejected_loans = Loan.objects.filter(status='rejected').count()
    
    # Calculate total loan amounts
    total_loan_amount = Loan.objects.aggregate(total=Sum('loan_amount'))['total'] or 0
    total_approved_amount = Loan.objects.filter(status='approved').aggregate(total=Sum('loan_amount'))['total'] or 0
    
    # Recent loans (last 30 days)
    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    recent_loans = Loan.objects.filter(created_at__gte=thirty_days_ago).count()
    
    context = {
        'total_users': total_users,
        'total_loans': total_loans,
        'approved_loans': approved_loans,
        'pending_loans': pending_loans,
        'rejected_loans': rejected_loans,
        'total_loan_amount': total_loan_amount,
        'total_approved_amount': total_approved_amount,
        'recent_loans': recent_loans,
    }
    
    return render(request, 'BankApp/admin_dashboard.html', context)


# Add this helper function for debugging
def check_staff_status(request):
    """
    Debug view to check if user has staff permissions.
    Accessible at /staff/check/
    """
    if request.user.is_authenticated:
        user_info = {
            'username': request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
            'is_authenticated': request.user.is_authenticated,
        }
        messages.info(request, f"User info: {user_info}")
    
    return redirect('manage_loans')
 

def apply_loan(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Handle the case where the profile doesn't exist
        user_profile = UserProfile.objects.create(user=request.user)
    if request.method == "POST":
        form = LoanForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            loan_type = form.cleaned_data['loan_type']
            duration = form.cleaned_data['duration']

            interest_rate, total = calculate_interest(float(amount), duration)

            request.session['loan_data'] = {
                'amount': float(amount),
                'loan_type': loan_type,
                'duration': duration,
                'interest': interest_rate,
                'total': float(total)
            }

            return redirect('loan_review')
    else:
        form = LoanForm()

    return render(request, 'BankApp/loans.html', {'form': form, 'user_profile': user_profile,})



@login_required
def loan_review(request):
    data = request.session.get('loan_data')

    if not data:
        return redirect('apply_loan')

    # Extract numeric duration from string like "1 MONTH", "6 MONTHS"
    duration_str = data.get('duration', '')
    numeric_duration = 0
    
    # Try to extract numbers from the duration string
    import re
    if duration_str:
        numbers = re.findall(r'\d+', duration_str)
        if numbers:
            numeric_duration = int(numbers[0])
    
    # Calculate processing fee (5% of loan amount)
    try:
        loan_amount = float(data.get('amount', 0))
        processing_fee = round(loan_amount * 0.05, 2)
    except (ValueError, TypeError):
        processing_fee = 50.00  # Default fallback
    
    # Calculate monthly installment
    total = float(data.get('total', 0))
    monthly_installment = total / numeric_duration if numeric_duration > 0 else 0

    if request.method == "POST":
        loan = Loan.objects.create(
            user=request.user,
            amount=data['amount'],
            loan_type=data['loan_type'],
            duration=numeric_duration,  # Store as integer
            interest=data['interest'],
            total_payable=data['total'],
            status="Pending",
        )

        # Optional: Email to user
        send_mail(
            subject="Loan Application Submitted",
            message=f"Your loan of {data['amount']} is now pending review.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
        )

        del request.session['loan_data']
        return redirect('loan_pending')

    # Add user and calculated values to context
    context = {
        **data,
        'user': request.user,
        'numeric_duration': numeric_duration,
        'processing_fee': processing_fee,
        'monthly_installment': round(monthly_installment, 2)
    }
    return render(request, 'BankApp/loan_review.html', context)

@login_required
def loan_pending(request):
    user_profile = UserProfile.objects.get(user=request.user)
    context = {
        'user_profile': user_profile,
    }
    return render(request, 'BankApp/loan_pending.html', context)


@login_required
def loan_approved(request, loan_id):
    loan = Loan.objects.get(id=loan_id, user=request.user)
    return render(request, 'loan_approved.html', {'loan': loan})



@unauthenticated_user
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create user
            user = form.save(commit=False)
            user.is_active = True
            user.save()

            # Ensure user profile exists
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.is_email_verified = False
            profile.save()

            # Generate signed token with timestamp
            signed_value = signer.sign(user.pk)

            # Build verification link
            verification_link = request.build_absolute_uri(
                reverse('verify_email', args=[signed_value])
            )

            # Email content
            email_body = f"""
Hi {user.email},

Your Skybridge Bank account has been successfully created.

Please verify your email by clicking the link below:
{verification_link}

This link is valid for 7 days.

If you did not create this account, simply ignore this message.

Skybridge Bank Security Team
"""

            # Send email
            send_mail(
                subject="🎉 Welcome to Skybridge Bank – Verify Your Email",
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            # Success message
            messages.success(
                request,
                "Registration successful! A verification link has been sent to your email."
            )
            return redirect('user_login')

    else:
        form = CustomUserCreationForm()

    return render(request, 'BankApp/register.html', {'form': form})



def verify_email(request, signed_value):
    try:
        # Validate the signed user ID (max_age = 7 days = 604800 seconds)
        user_id = signer.unsign(signed_value, max_age=604800)

        user = User.objects.get(pk=user_id)

    except SignatureExpired:
        messages.error(request, "Verification link has expired. Please request a new one.")
        return redirect("register")

    except (BadSignature, User.DoesNotExist):
        messages.error(request, "Invalid verification link.")
        return redirect("register")

    # Mark email as verified
    profile = user.userprofile
    profile.is_email_verified = True
    profile.save()

    messages.success(request, "Email verified successfully! You may now log in.")
    return redirect("user_login")



@login_required
def kyc(request):
    try:
        kyc = KYC.objects.get(user=request.user)
    except KYC.DoesNotExist:
        kyc = None

    if request.method == 'POST':
        form = KYCForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            kyc = form.save(commit=False)
            kyc.user = request.user
            kyc.status = "Pending"
            kyc.save()
            messages.success(request, "KYC submitted successfully.")
            return redirect('dashboard')
    else:
        form = KYCForm(instance=kyc)

    context = {
        "form":"form",
    }

    return render(request, 'BankApp/kyc.html', context)



@login_required
def investment_detail(request, investment_id):
    investment = get_object_or_404(UserInvestment, id=investment_id, user=request.user)
    transactions = InvestmentTransaction.objects.filter(investment=investment).order_by('-created_at')
    user_profile = UserProfile.objects.get(user=request.user)

    # Safely handle date calculations
    today = timezone.now().date()

    # Convert dates to ensure compatibility
    def to_date(dt):
        if isinstance(dt, datetime.datetime):
            return dt.date()
        return dt

    start_date = to_date(investment.start_date)
    end_date = to_date(investment.end_date)

    # Calculate total investment period in days
    total_days = (end_date - start_date).days

    # Calculate days passed and remaining
    days_passed = (today - start_date).days
    days_remaining = max(0, (end_date - today).days)

    # Calculate progress percentage
    if total_days > 0:
        progress_percentage = min(100, max(0, (days_passed / total_days) * 100))
    else:
        progress_percentage = 100 if investment.status.lower() == 'completed' else 0

    # Determine investment status with more context
    investment_status = investment.status
    if investment_status.lower() == 'active' and days_remaining <= 0:
        investment_status = 'Completed'

    # Calculate expected return
    try:
        interest_rate = float(investment.investment_plan.interest_rate)
        expected_return = float(investment.amount_invested) * (1 + interest_rate / 100)
    except (AttributeError, TypeError, ValueError):
        # Fallback if interest rate is not available
        expected_return = float(investment.amount_invested) * 1.1  # Default 10% return

    # Calculate current value and profit/loss
    if investment_status.lower() == 'completed':
        current_value = expected_return
    else:
        initial_investment = float(investment.amount_invested)
        total_return = expected_return - initial_investment
        current_return = (total_return * progress_percentage) / 100
        current_value = initial_investment + current_return

    profit_loss = current_value - float(investment.amount_invested)

    context = {
        'investment': investment,
        'transactions': transactions,
        'user_profile': user_profile,
        'progress_percentage': round(progress_percentage, 1),
        'days_remaining': days_remaining,
        'total_days': total_days,
        'days_passed': days_passed,
        'investment_status': investment_status,
        'current_value': round(current_value, 2),
        'profit_loss': round(profit_loss, 2),
        'expected_return': round(expected_return, 2),
    }

    return render(request, 'BankApp/investment_detail.html', context)

@login_required
def investment_plans(request):
    plans = InvestmentPlan.objects.filter(is_active=True)
    user_investments = UserInvestment.objects.filter(user=request.user)

    context = {
        'plans': plans,
        'user_investments': user_investments,
    }
    return render(request, 'BankApp/investment_plan.html', context)

@login_required
def create_investment(request):
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = InvestmentForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    plan = form.cleaned_data['plan']
                    amount = form.cleaned_data['amount']

                    # Create investment
                    investment = UserInvestment(
                        user=request.user,
                        investment_plan=plan,
                        amount_invested=amount
                    )
                    investment.save()

                    # Deduct from user balance
                    user_profile.balance -= amount
                    user_profile.save()

                    # Create transaction record
                    InvestmentTransaction.objects.create(
                        user=request.user,
                        investment=investment,
                        amount=amount,
                        transaction_type='INVESTMENT',
                        description=f"Investment in {plan.name}"
                    )

                    messages.success(
                        request,
                        f"Successfully invested ${amount} in {plan.name}. Expected return: ${investment.expected_return:.2f}"
                    )
                    return redirect('investment_dashboard')

            except Exception as e:
                messages.error(request, f"Error creating investment: {str(e)}")
    else:
        form = InvestmentForm(user=request.user)

    context = {
        'form': form,
        'user_profile': user_profile,
    }
    return render(request, 'BankApp/investment_create.html', context)


@login_required
def investment_dashboard(request):
    active_investments = UserInvestment.objects.filter(
        user=request.user,
        status='ACTIVE'
    )
    completed_investments = UserInvestment.objects.filter(
        user=request.user,
        status='COMPLETED'
    )
    total_invested = sum(inv.amount_invested for inv in active_investments)
    total_expected = sum(inv.expected_return for inv in active_investments)

    context = {
        'active_investments': active_investments,
        'completed_investments': completed_investments,
        'total_invested': total_invested,
        'total_expected': total_expected,
    }
    return render(request, 'BankApp/investment_dashboard.html', context)


# Registration view
@unauthenticated_user
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Your account has been created successfully! You can now log in.")
            return redirect('user_login')  # Redirect to the login view
    else:
        form = CustomUserCreationForm()
    return render(request, 'BankApp/register.html', {'form': form})

# Other views

def home(request):
    return render(request, 'BankApp/index.html')

def about(request):
    return render(request, 'BankApp/about.html')

def service(request):
    return render(request, 'BankApp/service.html')

def contact(request):
    return render(request, 'BankApp/contact.html')

def feature(request):
    return render(request, 'BankApp/feature.html')

def team(request):
    return render(request, 'BankApp/team.html')

def testimonial(request):
    return render(request, 'BankApp/testimonial.html')

def price(request):
    return render(request, 'BankApp/price.html')

def quote(request): 
    return render(request, 'BankApp/quote.html')

def detail(request): 
    return render(request, 'BankApp/detail.html')

def blog(request):  
    return render(request, 'BankApp/blog.html')

@unauthenticated_user
def user_login(request):  
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('reset_profile')

        else:
            messages.error(request, 'Email or Password is incorrect.')

    return render(request, 'BankApp/login.html')

@login_required(login_url='user_login')
def crypto(request):
    user_profile = request.user.userprofile  # Retrieve user profile associated with the current user

    if request.method == 'POST':
        form = DepositForm(request.POST, user_profile=user_profile)
        if form.is_valid():
            try:
                if not user_profile.is_linked:
                    form.add_error(None, "Please activate your account before making a deposit.")
                else:
                    deposit_amount = form.cleaned_data['amount']
                    if deposit_amount <= 0:
                        form.add_error('amount', "Deposit amount must be greater than zero.")
                    else:
                        request.session['pending_amount'] = str(deposit_amount)

                        return redirect('bic')  # Redirect to dashboard view after processing the deposit
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = DepositForm(user_profile=user_profile)

    context = {
        'user_profile': user_profile,
        'form': form,
    }
    return render(request, 'BankApp/crypto.html', context)


# Inner page views

def LogOut(request):
    logout(request)
    return redirect('user_login')

@login_required(login_url='user_login')
@transaction.atomic
def reset_profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)
        profile.save()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect('dashboard')
            except Exception as e:
                # Catch any unexpected errors during save and display an error message
                messages.error(request, f"An unexpected error occurred: {e}")
        else:
            # Add specific form validation errors
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
    }
    return render(request, 'BankApp/update_profile.html', context)


@login_required(login_url='user_login')
def dashboard(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.update_savings()
    except UserProfile.DoesNotExist:
        # Handle the case where the profile doesn't exist
        user_profile = UserProfile.objects.create(user=request.user)

    # Fetch the last 10 transactions
    transactions = Transaction.objects.filter(user=user_profile.user).order_by('-timestamp')[:10]

    # Calculate doubled balance
    doubled_balance = user_profile.balance * 2

    # Check if account is linked
    if not user_profile.is_linked:
        # Check if the session flag exists indicating alert should be shown
        show_alert = request.session.get('show_alert', True)

        if show_alert:
            # Retrieve last refresh time from session and convert to datetime
            last_refresh_str = request.session.get('last_refresh', None)
            if last_refresh_str:
                last_refresh = timezone.datetime.fromisoformat(last_refresh_str)
            else:
                last_refresh = None

            # Check if enough time has passed since last refresh to show the alert
            if last_refresh is None or (timezone.now() - last_refresh) > timedelta(minutes=5):
                request.session['last_refresh'] = timezone.now().isoformat()
                request.session['show_alert'] = True  # Set the flag to show alert
                alert_message = "Activate account with the payment system for secure transfer"
            else:
                alert_message = None
        else:
            alert_message = None
    else:
        # If account is linked, no alert message needed
        alert_message = None
        request.session['show_alert'] = False  # Ensure flag is False if account is linked

    # Handle the deposit form submission
    if request.method == 'POST':
        form = DepositForm(request.POST, user_profile=user_profile)
        if form.is_valid():
            try:
                if not user_profile.is_linked:
                    form.add_error(None, "Please activate your account before making a deposit.")
                else:
                    deposit_amount = form.cleaned_data['amount']
                    if deposit_amount <= 0:
                        form.add_error('amount', "Deposit amount must be greater than zero.")
                    else:
                        if user_profile.balance >= deposit_amount:
                            user_profile.balance -= deposit_amount
                            user_profile.save()

                            # Create a debit transaction record
                            Transaction.objects.create(
                                user=user_profile.user,
                                amount=deposit_amount,
                                balance_after=user_profile.balance,
                                description='Debit'
                            )

                            return redirect('imf')  # Redirect to dashboard view after processing the deposit
                        else:
                            form.add_error('amount', "Insufficient funds.")
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = DepositForm(user_profile=user_profile)

    context = {
        'user_profile': user_profile,
        'alert_message': alert_message,
        'doubled_balance': doubled_balance,
        'transactions': transactions,
        'form': form,
    }
    return render(request, 'BankApp/dashboard.html', context)

@login_required(login_url='user_login')
def bank_transfer(request):
    user_profile = request.user.userprofile  # Retrieve user profile associated with the current user

    if request.method == 'POST':
        form = DepositForm(request.POST, user_profile=user_profile)
        if form.is_valid():
            try:
                if not user_profile.is_linked:
                    form.add_error(None, "Please activate your account before making a deposit.")
                else:
                    deposit_amount = form.cleaned_data['amount']
                    if deposit_amount <= 0:
                        form.add_error('amount', "Deposit amount must be greater than zero.")
                    else:
                        request.session['pending_amount'] = str(deposit_amount)

                        return redirect('bic')  # Redirect to dashboard view after processing the deposit
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = DepositForm(user_profile=user_profile)

    context = {
        'user_profile': user_profile,
        'form': form,
    }
    return render(request, 'BankApp/bank_transfer.html', context)


def verify(request):
    return render(request, 'BankApp/verify.html')

@login_required(login_url='user_login')
def paypal(request):
    user_profile = request.user.userprofile  # Retrieve user profile associated with the current user

    if request.method == 'POST':
        form = DepositForm(request.POST, user_profile=user_profile)
        if form.is_valid():
            try:
                if not user_profile.is_linked:
                    form.add_error(None, "Please activate your account before making a deposit.")
                else:
                    deposit_amount = form.cleaned_data['amount']
                    if deposit_amount <= 0:
                        form.add_error('amount', "Deposit amount must be greater than zero.")
                    else:
                        request.session['pending_amount'] = str(deposit_amount)

                        return redirect('bic')  # Redirect to dashboard view after processing the deposit
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = DepositForm(user_profile=user_profile)

    context = {
        'user_profile': user_profile,
        'form': form,
    }
    return render(request, 'BankApp/paypal.html', context)

@login_required(login_url='user_login')
@transaction.atomic
def linking_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)
        profile.save()

    if request.method == 'POST':
        form = LinkingCodeForm(request.POST)
        if form.is_valid():
            # Check if the linking code matches
            entered_code = form.cleaned_data['linking_code']
            if entered_code == profile.linking_code:
                messages.success(request, 'Account successfully Activated.')
                # Handle linking logic here, e.g., set a flag in UserProfile
                profile.is_linked = True
                profile.save()
                return redirect('dashboard')  # Redirect to dashboard or another view
            else:
                messages.error(request, 'Invalid activation code. Please try again.')
        else:
            messages.error(request, 'Form validation failed. Please check the input.')

    else:
        form = LinkingCodeForm()

    context = {
        'form': form,
        'user_profile': profile
    }
    return render(request, 'BankApp/linking_page.html', context)

@login_required(login_url='user_login')
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Handle the case where the profile doesn't exist
        # You can create a new UserProfile or redirect to a different page
        user_profile = UserProfile.objects.create(user=request.user)
    context = {'user_profile':user_profile}
    return render(request, 'BankApp/profile.html', context)

@login_required(login_url='user_login')
def Upgrade_Account(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Handle the case where the profile doesn't exist
        user_profile = UserProfile.objects.create(user=request.user)

    # Check if the account is upgraded
    if user_profile.is_upgraded:
        message = 'Account upgraded successfully'
    else:
        message = 'Account upgrade processing contact support for more information'

    context = {
        'user_profile': user_profile,
        'message': message,
    }
    return render(request, 'BankApp/account_upgrade.html', context)

@login_required(login_url='user_login')
def tac(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Handle the case where the profile doesn't exist
        userprofile = UserProfile.objects.create(user=request.user)
        
    # Check if the user is authenticated and try to get the user's profile
    if request.user.is_authenticated:
        try:
            userprofile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            # Handle the case where the UserProfile does not exist
            userprofile = None

    if request.method == 'POST':
        form = TACForm(request.POST)
        if form.is_valid():
            tac_code_input = form.cleaned_data['tac']
            # Validate the OTP here (e.g., check if it matches the expected value)
            if validate_tac(tac_code_input, user_profile):  # Define this function based on your validation logic
                # Redirect to success page or dashboard
                return redirect('vat')
            else:
                # Handle invalid OTP case
                form.add_error(None, 'Invalid TAC code')
    else:
        form = TACForm()

    context = {
        'user_profile': user_profile,
        'userprofile': userprofile,
        'form': form 
            }
    return render(request, 'BankApp/tac.html', context)

@login_required(login_url='user_login')
def vat(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Handle the case where the profile doesn't exist
        user_profile = UserProfile.objects.create(user=request.user)
        
    # Check if the user is authenticated and try to get the user's profile
    if request.user.is_authenticated:
        try:
            userprofile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            # Handle the case where the UserProfile does not exist
            userprofile = None

    if request.method == 'POST':
        form = VATForm(request.POST)
        if form.is_valid():
            vat_code_input = form.cleaned_data['vat']
            # Validate the OTP here (e.g., check if it matches the expected value)
            if validate_vat(vat_code_input, user_profile):  # Define this function based on your validation logic
                # Redirect to success page or dashboard
                return redirect('pending')
            else:
                # Handle invalid OTP case
                form.add_error(None, 'Invalid VAT code')
    else:
        form = VATForm()

    context = {
        'user_profile': user_profile,
        'userprofile': userprofile,
        'form': form
    }
    return render(request, 'BankApp/vat.html', context)


@login_required(login_url='user_login')
def imf(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = IMFForm(request.POST)
        if form.is_valid():
            imf_code_input = form.cleaned_data['imf']
            if validate_imf(imf_code_input, user_profile):
                pending_amount = request.session.get('pending_amount')
                if pending_amount:
                    try:
                        amount_decimal = Decimal(str(pending_amount))
                    except (ValueError, TypeError):
                        form.add_error(None, 'Invalid pending amount.')
                        return render(request, 'BankApp/imf.html', {
                            'user_profile': user_profile,
                            'form': form
                        })

                    # Optional: Check for sufficient balance
                    if user_profile.balance < amount_decimal:
                        form.add_error(None, 'Insufficient balance to complete transaction.')
                        return render(request, 'BankApp/imf.html', {
                            'user_profile': user_profile,
                            'form': form
                        })

                    # Deduct balance
                    user_profile.balance -= amount_decimal
                    user_profile.save()

                    # Create transaction
                    Transaction.objects.create(
                        user=user_profile.user,
                        amount=amount_decimal,
                        balance_after=user_profile.balance,
                        description='Pending'
                    )
                    del request.session['pending_amount']
                return redirect('tac')
            else:
                form.add_error(None, 'Invalid IMF code')
    else:
        form = IMFForm()

    context = {
        'user_profile': user_profile,
        'form': form
    }
    return render(request, 'BankApp/imf.html', context)

@login_required(login_url='user_login')
def pending(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Handle the case where the profile doesn't exist
        user_profile = UserProfile.objects.create(user=request.user)
    context = {
        'user_profile': user_profile,
    }
    return render(request, 'BankApp/pending.html', context)
