# Generated by Django 4.2.5 on 2023-09-15 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='sendpulse_id',
            field=models.CharField(blank=True, max_length=128, verbose_name='sendpulse id'),
        ),
        migrations.AddField(
            model_name='businessunit',
            name='sendpulse_secret',
            field=models.CharField(blank=True, max_length=128, verbose_name='sendpulse secret'),
        ),
    ]
