# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0027_glossaryterm'),
    ]

    operations = [
        migrations.AddField(
            model_name='glossaryterm',
            name='description',
            field=models.TextField(default=[]),
        ),
    ]
