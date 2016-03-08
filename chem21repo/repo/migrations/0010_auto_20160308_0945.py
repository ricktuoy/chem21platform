# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0009_topic_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='quiz_name',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='module',
            name='quiz_name',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='quiz_name',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='quiz_name',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='quiz_name',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
