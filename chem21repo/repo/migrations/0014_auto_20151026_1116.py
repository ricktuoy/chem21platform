# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0013_module_files'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='ext',
            field=models.CharField(max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='path',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
