# Generated by Django 5.1.2 on 2024-10-31 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BankApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='annual_income',
            field=models.DecimalField(choices=[('below_20k', 'Below $20,000'), ('20k_40k', '$20,000 - $40,000'), ('40k_60k', '$40,000 - $60,000'), ('60k_80k', '$60,000 - $80,000'), ('80k_100k', '$80,000 - $100,000'), ('100k_150k', '$100,000 - $150,000'), ('150k_above', 'Above $150,000')], decimal_places=3, default=0.0, max_digits=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='four_digit_auth_key',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='occupation',
            field=models.CharField(blank=True, choices=[('management', 'Management'), ('business_finance', 'Business and Financial Operations'), ('computer_math', 'Computer and Mathematical'), ('architecture_engineering', 'Architecture and Engineering'), ('life_sciences', 'Life, Physical, and Social Sciences'), ('community_social', 'Community and Social Service'), ('legal', 'Legal'), ('education', 'Education, Training, and Library'), ('arts_design', 'Arts, Design, Entertainment, Sports, and Media'), ('healthcare', 'Healthcare Practitioners and Technical')], default='select your occupation', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='two_factor_auth',
            field=models.CharField(choices=[('enable', 'Enable'), ('disable', 'Disable')], default='disable', max_length=10),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='zip_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]