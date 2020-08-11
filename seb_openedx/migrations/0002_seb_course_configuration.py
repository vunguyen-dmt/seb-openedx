# Generated by Django 2.2.12 on 2020-05-08 22:41
# pylint: disable=invalid-name
"""Migration."""

from django.db import migrations, models
import opaque_keys.edx.django.models


class Migration(migrations.Migration):
    """Add course configuration table."""

    dependencies = [
        ('seb_openedx', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SebCourseConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(max_length=255, unique=True)),
                ('permission_components', models.TextField(blank=True, default='')),
                ('browser_keys', models.TextField(blank=True, default='')),
                ('config_keys', models.TextField(blank=True, default='')),
                ('user_banning_enabled', models.BooleanField(default=False)),
                ('blacklist_chapters', models.TextField(blank=True, default='')),
                ('whitelist_paths', models.TextField(blank=True, default='')),
            ],
        ),
    ]