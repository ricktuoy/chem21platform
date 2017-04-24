# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0029_auto_20170421_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='page',
            field=models.ForeignKey(blank=True, to='repo.Question', null=True),
        ),
        migrations.AddField(
            model_name='module',
            name='page',
            field=models.ForeignKey(blank=True, to='repo.Question', null=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='page',
            field=models.ForeignKey(blank=True, to='repo.Question', null=True),
        ),
    ]
