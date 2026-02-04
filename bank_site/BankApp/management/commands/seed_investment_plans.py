from django.core.management.base import BaseCommand
from BankApp.models import InvestmentPlan
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed investment plans data'
    
    def handle(self, *args, **kwargs):
        plans_data = [
            # Starter Plan - Short Term
            {
                'name': 'Starter Plan - 6 Hours',
                'plan_type': 'STARTER',
                'investment_type': 'SHORT_TERM',
                'min_amount': Decimal('100.00'),
                'max_amount': Decimal('500.00'),
                'min_profit_percentage': Decimal('6.00'),
                'max_profit_percentage': Decimal('10.00'),
                'duration_days': 0,
                'interval_hours': 6,
                'description': 'Starter short-term trading with 6-hour intervals. Profit: 6-10%',
                'is_active': True
            },
            # Starter Plan - Long Term
            {
                'name': 'Starter Plan - 14 Days',
                'plan_type': 'STARTER',
                'investment_type': 'LONG_TERM',
                'min_amount': Decimal('500.00'),
                'max_amount': Decimal('2000.00'),
                'min_profit_percentage': Decimal('18.00'),
                'max_profit_percentage': Decimal('25.00'),
                'duration_days': 14,
                'interval_hours': None,
                'description': 'Starter long-term investment for 14 days. Profit: 18-25%',
                'is_active': True
            },
            # Pro Plan - Short Term
            {
                'name': 'Pro Plan - 12 Hours',
                'plan_type': 'PRO',
                'investment_type': 'SHORT_TERM',
                'min_amount': Decimal('500.00'),
                'max_amount': Decimal('2000.00'),
                'min_profit_percentage': Decimal('10.00'),
                'max_profit_percentage': Decimal('15.00'),
                'duration_days': 0,
                'interval_hours': 12,
                'description': 'Pro medium-term trading with 12-hour intervals. Profit: 10-15%',
                'is_active': True
            },
            # Pro Plan - Long Term
            {
                'name': 'Pro Plan - 30 Days',
                'plan_type': 'PRO',
                'investment_type': 'LONG_TERM',
                'min_amount': Decimal('2000.00'),
                'max_amount': Decimal('5000.00'),
                'min_profit_percentage': Decimal('25.00'),
                'max_profit_percentage': Decimal('35.00'),
                'duration_days': 30,
                'interval_hours': None,
                'description': 'Pro long-term investment for 30 days. Profit: 25-35%',
                'is_active': True
            },
            # Elite Plan - Short Term
            {
                'name': 'Elite Plan - 24 Hours',
                'plan_type': 'ELITE',
                'investment_type': 'SHORT_TERM',
                'min_amount': Decimal('2000.00'),
                'max_amount': Decimal('10000.00'),
                'min_profit_percentage': Decimal('15.00'),
                'max_profit_percentage': Decimal('20.00'),
                'duration_days': 0,
                'interval_hours': 24,
                'description': 'Elite high-yield trading with 24-hour intervals. Profit: 15-20%',
                'is_active': True
            },
            # Elite Plan - Long Term
            {
                'name': 'Elite Plan - 60 Days',
                'plan_type': 'ELITE',
                'investment_type': 'LONG_TERM',
                'min_amount': Decimal('5000.00'),
                'max_amount': Decimal('20000.00'),
                'min_profit_percentage': Decimal('35.00'),
                'max_profit_percentage': Decimal('50.00'),
                'duration_days': 60,
                'interval_hours': None,
                'description': 'Elite long-term investment for 60 days. Profit: 35-50%',
                'is_active': True
            },
        ]
        
        created_count = 0
        for plan_data in plans_data:
            plan, created = InvestmentPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created plan: {plan.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created/updated {created_count} investment plans'))