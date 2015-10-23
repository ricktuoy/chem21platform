# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0011_uniquefile_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uniquefile',
            name='size',
            field=models.BigIntegerField(default=0),
        ),
    ]
