# Generated by Django 4.2.5 on 2023-09-16 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0005_businessunit_google_creds'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessunit',
            name='last_update_sendpulse',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]