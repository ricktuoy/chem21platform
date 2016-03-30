# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0011_module_is_question'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='is_question',
            field=models.BooleanField(default=False),
        ),
    ]
