# Generated by Django 4.2.5 on 2023-09-16 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0004_alter_businessunit_sendpulse_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='google_creds',
            field=models.FileField(null=True, upload_to='google_creds/', verbose_name='google credentials'),
        ),
    ]
