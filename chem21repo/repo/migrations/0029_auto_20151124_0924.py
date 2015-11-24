# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0028_uniquefile_remote_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='dirty',
            field=models.TextField(default=b'[]'),
        ),
        migrations.AddField(
            model_name='module',
            name='dirty',
            field=models.TextField(default=b'[]'),
        ),
        migrations.AddField(
            model_name='question',
            name='dirty',
            field=models.TextField(default=b'[]'),
        ),
    ]
