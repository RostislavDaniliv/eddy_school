# Generated by Django 4.2.5 on 2023-10-02 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0011_businessunit_bot_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='sendpulse_chain_id',
            field=models.CharField(blank=True, max_length=128, verbose_name='sendpulse chain id'),
        ),
    ]