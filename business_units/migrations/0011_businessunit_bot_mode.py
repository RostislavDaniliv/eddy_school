# Generated by Django 4.2.5 on 2023-10-02 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0010_businessunit_max_tokens'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit',
            name='bot_mode',
            field=models.PositiveIntegerField(choices=[(1, 'Strict mode'), (2, 'Manager chain'), (3, 'Soft mode')], default=1, verbose_name='bot mode'),
        ),
    ]