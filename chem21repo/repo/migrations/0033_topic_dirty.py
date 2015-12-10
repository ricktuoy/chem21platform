# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0032_module-power'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='dirty',
            field=models.TextField(default=b'[]'),
        ),
    ]
