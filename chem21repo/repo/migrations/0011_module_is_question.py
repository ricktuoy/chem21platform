# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0010_auto_20160308_0945'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='is_question',
            field=models.BooleanField(default=False),
        ),
    ]
