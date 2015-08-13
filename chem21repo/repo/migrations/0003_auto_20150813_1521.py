# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0002_auto_20150813_1513'),
    ]

    operations = [
        migrations.AlterField(
            model_name='path',
            name='name',
            field=models.CharField(unique=True, max_length=800),
        ),
    ]
