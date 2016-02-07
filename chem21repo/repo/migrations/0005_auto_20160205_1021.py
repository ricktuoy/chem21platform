# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0004_auto_20160203_1740'),
    ]

    operations = [
        migrations.AlterField(
            model_name='biblio',
            name='citekey',
            field=models.CharField(unique=True, max_length=300),
        ),
        migrations.AlterField(
            model_name='biblio',
            name='display_string',
            field=models.CharField(default=b'', max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='biblio',
            name='title',
            field=models.CharField(default=b'', max_length=500, blank=True),
        ),
    ]
