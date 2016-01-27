# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0041_auto_20160105_1907'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uniquefile',
            name='authors',
        ),
        migrations.AddField(
        	model_name='uniquefile',
            name='authors',
            field=models.ManyToManyField(to='repo.Author'),
        ),
    ]
