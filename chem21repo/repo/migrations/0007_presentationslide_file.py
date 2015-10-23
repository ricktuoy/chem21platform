# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import filebrowser.fields


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0006_auto_20151023_0957'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentationslide',
            name='file',
            field=filebrowser.fields.FileBrowseField(max_length=50, null=True),
        ),
    ]
