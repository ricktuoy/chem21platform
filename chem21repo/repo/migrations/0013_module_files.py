# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0012_auto_20151023_1458'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='files',
            field=models.ManyToManyField(to='repo.UniqueFile', through='repo.UniqueFilesofModule'),
        ),
    ]
