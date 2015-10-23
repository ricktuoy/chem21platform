# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0009_auto_20151023_1244'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='ready',
            field=models.BooleanField(default=False),
        ),
    ]
