# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0004_auto_20150819_1218'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='file',
            name='checksum',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='file',
            name='cut_of',
            field=models.ForeignKey(related_name='cuts', to='repo.File', null=True),
        ),
    ]
