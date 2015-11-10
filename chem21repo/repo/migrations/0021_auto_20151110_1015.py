# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0020_auto_20151109_1122'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='remote_id',
            field=models.IntegerField(null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='module',
            name='remote_id',
            field=models.IntegerField(null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='question',
            name='remote_id',
            field=models.IntegerField(null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='presentations',
            field=models.ManyToManyField(to='repo.Presentation', through='repo.PresentationsInQuestion'),
        ),
    ]
