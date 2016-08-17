# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0023_auto_20160815_1059'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='biblio',
            name='ISSN',
        ),
    ]
