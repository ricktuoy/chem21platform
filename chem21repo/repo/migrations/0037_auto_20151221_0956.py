# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0036_auto_20151219_1548'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='dirty',
            field=models.TextField(default=b'[]'),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='remote_id',
            field=models.IntegerField(null=True, db_index=True),
        ),
    ]
