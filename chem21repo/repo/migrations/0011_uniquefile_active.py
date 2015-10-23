# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0010_uniquefile_ready'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
