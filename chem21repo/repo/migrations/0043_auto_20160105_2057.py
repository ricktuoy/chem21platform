# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0042_auto_20160105_1925'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='text',
            field=tinymce.models.HTMLField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='uniquefile',
            name='authors',
            field=models.ManyToManyField(to='repo.Author', blank=True),
        ),
        migrations.AlterField(
            model_name='uniquefile',
            name='remote_path',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
