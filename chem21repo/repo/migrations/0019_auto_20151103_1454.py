# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0018_uniquefilesofmodule_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='uniquefilesofmodule',
            options={'ordering': ('order',)},
        ),
    ]
