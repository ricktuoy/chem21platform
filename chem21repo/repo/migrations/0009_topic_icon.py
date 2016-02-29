# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import filebrowser.fields


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0008_auto_20160222_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='icon',
            field=filebrowser.fields.FileBrowseField(max_length=500, null=True),
        ),
    ]
