# Generated by Django 5.1.2 on 2024-11-02 13:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('BankApp', '0004_alter_userprofile_four_digit_auth_key_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='annual_income',
        ),
    ]
