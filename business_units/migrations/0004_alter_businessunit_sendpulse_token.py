# Generated by Django 4.2.5 on 2023-09-15 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0003_businessunit_last_update_sendpulse_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessunit',
            name='sendpulse_token',
            field=models.TextField(blank=True, verbose_name='sendpulse token'),
        ),
    ]
