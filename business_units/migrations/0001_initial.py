# Generated by Django 4.2.5 on 2023-09-15 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apikey', models.CharField(blank=True, max_length=128, verbose_name='apikey')),
                ('name', models.CharField(blank=True, max_length=100, null=True, verbose_name='name')),
                ('gpt_api_key', models.CharField(blank=True, max_length=300, null=True, verbose_name='gpt api key')),
                ('documents_list', models.TextField(blank=True, verbose_name='documents list')),
            ],
        ),
    ]
