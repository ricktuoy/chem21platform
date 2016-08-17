# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0022_auto_20160708_1024'),
    ]

    operations = [
        migrations.AddField(
            model_name='biblio',
            name='DOI',
            field=models.CharField(max_length=300, unique=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='biblio',
            name='ISSN',
            field=models.CharField(max_length=300, unique=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='biblio',
            name='bibkey',
            field=models.CharField(max_length=300, unique=True, null=True, blank=True),
        ),
    ]
