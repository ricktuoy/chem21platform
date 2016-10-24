# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0026_auto_20161020_1139'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlossaryTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, db_index=True)),
            ],
        ),
    ]
