# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0017_uniquefile_cut_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefilesofmodule',
            name='order',
            field=models.IntegerField(default=0),
        ),
    ]
