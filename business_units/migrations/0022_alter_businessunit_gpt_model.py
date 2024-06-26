# Generated by Django 4.2.5 on 2023-10-10 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0021_alter_businessunit_gpt_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessunit',
            name='gpt_model',
            field=models.CharField(choices=[('gpt-3.5-turbo', 'Gpt 3.5'), ('gpt-4', 'Gpt 4')], default='gpt-3.5-turbo', verbose_name='GPT model'),
        ),
    ]
