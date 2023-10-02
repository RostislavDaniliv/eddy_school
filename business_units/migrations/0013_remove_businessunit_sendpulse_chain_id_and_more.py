# Generated by Django 4.2.5 on 2023-10-02 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_units', '0012_businessunit_sendpulse_chain_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='businessunit',
            name='sendpulse_chain_id',
        ),
        migrations.AddField(
            model_name='businessunit',
            name='sendpulse_flow_id',
            field=models.CharField(blank=True, max_length=128, verbose_name='sendpulse flow id'),
        ),
        migrations.AlterField(
            model_name='businessunit',
            name='bot_mode',
            field=models.PositiveIntegerField(choices=[(1, 'Strict mode'), (2, 'Manager flow'), (3, 'Soft mode')], default=1, verbose_name='bot mode'),
        ),
    ]
