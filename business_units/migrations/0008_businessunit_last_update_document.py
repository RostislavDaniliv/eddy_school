# Generated by Django 4.2.5 on 2023-09-21 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0007_businessunit_default_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='last_update_document',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]