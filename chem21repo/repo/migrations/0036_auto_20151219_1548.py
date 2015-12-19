# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0035_auto_20151211_1443'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='files'
        ),
        migrations.AddField(
            model_name='question',
            name='files',
            field=models.ManyToManyField(to='repo.UniqueFile'),
        ),
        migrations.AlterField(
            model_name='question',
            name='text',
            field=tinymce.models.HTMLField(default=b'', null=True, blank=True),
        ),
    ]
