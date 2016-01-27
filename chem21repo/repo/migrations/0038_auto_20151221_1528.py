# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0037_auto_20151221_0956'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='byline',
            field=tinymce.models.HTMLField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='files',
            field=models.ManyToManyField(related_name='questions', to='repo.UniqueFile'),
        ),
    ]
