# Generated by Django 4.2.15 on 2024-10-31 21:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0011_facilitator_attending_networking_session'),
    ]

    operations = [
        migrations.AddField(
            model_name='facilitator',
            name='position',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
