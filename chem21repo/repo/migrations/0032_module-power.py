# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0031_auto_20151125_1541'),
    ]

    operations = [
        migrations.CreateModel(
            name='module-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.module',),
        ),
    ]
