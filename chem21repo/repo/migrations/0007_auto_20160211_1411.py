# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0006_auto_20160209_0858'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='pdf',
        ),
        migrations.AddField(
            model_name='lesson',
            name='changed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='module',
            name='changed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='changed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='topic',
            name='changed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='changed',
            field=models.BooleanField(default=False),
        ),
    ]
