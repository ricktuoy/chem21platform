# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0016_auto_20151103_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='cut_order',
            field=models.IntegerField(default=0),
        ),
    ]
