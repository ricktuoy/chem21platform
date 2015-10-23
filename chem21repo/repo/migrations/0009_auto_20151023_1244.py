# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0008_auto_20151023_1004'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UniqueFileofModule',
            new_name='UniqueFilesofModule',
        ),
    ]
