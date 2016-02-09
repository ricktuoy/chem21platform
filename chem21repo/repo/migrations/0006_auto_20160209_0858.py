# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0005_auto_20160205_1021'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='text',
            field=tinymce.models.HTMLField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='module',
            name='files',
            field=models.ManyToManyField(related_name='modules', through='repo.UniqueFilesofModule', to='repo.UniqueFile'),
        ),
    ]
