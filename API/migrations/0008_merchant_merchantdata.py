# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-07-23 10:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('API', '0007_auto_20170623_0527'),
    ]

    operations = [
        migrations.AddField(
            model_name='merchant',
            name='merchantData',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
