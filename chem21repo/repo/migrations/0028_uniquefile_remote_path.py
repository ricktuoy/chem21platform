# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0027_auto_20151111_1123'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='remote_path',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
