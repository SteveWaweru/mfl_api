# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-10-21 13:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0017_facility_reporting_in_dhis'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facility',
            name='reporting_in_dhis',
            field=models.NullBooleanField(help_text=b'A flag to indicate whether facility should have reporting in dhis'),
        ),
    ]
