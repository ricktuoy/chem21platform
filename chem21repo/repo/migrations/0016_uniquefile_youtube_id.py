# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0015_auto_20160412_1613'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='youtube_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]
