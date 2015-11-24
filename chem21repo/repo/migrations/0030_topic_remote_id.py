# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0029_auto_20151124_0924'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='remote_id',
            field=models.IntegerField(null=True, db_index=True),
        ),
    ]
