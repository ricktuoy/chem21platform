# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0002_textversion_modified_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='textversion',
            name='published',
            field=models.BooleanField(default=False),
        ),
    ]
