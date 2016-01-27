# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0039_uniquefile_version_of'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='text',
            field=tinymce.models.HTMLField(default=b'', null=True, blank=True),
        ),
    ]
