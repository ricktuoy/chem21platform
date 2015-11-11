# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0026_auto_20151111_0942'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filesinquestion',
            name='working',
        ),
        migrations.AddField(
            model_name='filesinquestion',
            name='product',
            field=models.BooleanField(default=False),
        ),
    ]
