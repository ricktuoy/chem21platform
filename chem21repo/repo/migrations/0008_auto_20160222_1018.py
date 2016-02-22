# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0007_auto_20160211_1411'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='dummy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='module',
            name='dummy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='dummy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='topic',
            name='dummy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='dummy',
            field=models.BooleanField(default=False),
        ),
    ]
