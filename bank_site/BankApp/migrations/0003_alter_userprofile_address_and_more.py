# Generated by Django 5.1.2 on 2024-10-31 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BankApp', '0002_userprofile_address_userprofile_annual_income_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='address',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='four_digit_auth_key',
            field=models.IntegerField(blank=True, max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='zip_code',
            field=models.IntegerField(blank=True, max_length=10, null=True),
        ),
    ]
