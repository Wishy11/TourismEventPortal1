# Generated by Django 5.1 on 2024-10-21 16:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('PahangPrism', '0002_alter_event_eventid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='image_path',
        ),
        migrations.RemoveField(
            model_name='venue',
            name='image_path',
        ),
    ]
