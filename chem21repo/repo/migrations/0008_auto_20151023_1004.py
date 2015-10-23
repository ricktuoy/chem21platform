# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import filebrowser.fields


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0007_presentationslide_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presentationslide',
            name='file',
            field=filebrowser.fields.FileBrowseField(max_length=500, null=True),
        ),
    ]
