# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0003_auto_20150813_1521'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='file',
            options={'ordering': ['containing_path__topic', 'containing_path__module']},
        ),
        migrations.AddField(
            model_name='file',
            name='file',
            field=models.FileField(null=True, upload_to=b''),
        ),
    ]
