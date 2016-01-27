# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0038_auto_20151221_1528'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='version_of',
            field=models.ForeignKey(related_name='versions', to='repo.UniqueFile', null=True),
        ),
    ]
