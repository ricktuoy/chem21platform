# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0014_auto_20151026_1116'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='s3d',
            field=models.BooleanField(default=False),
        ),
    ]
