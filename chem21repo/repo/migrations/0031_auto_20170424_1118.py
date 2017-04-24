# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0030_auto_20170424_1029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='files',
            field=models.ManyToManyField(related_name='questions', to='repo.UniqueFile', blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='lessons',
            field=models.ManyToManyField(related_name='questions', to='repo.Lesson', blank=True),
        ),
    ]
