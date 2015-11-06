# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0015_uniquefile_s3d'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='module',
            options={'ordering': ('order',)},
        ),
        migrations.AlterModelOptions(
            name='presentationslide',
            options={'ordering': ('order',)},
        ),
        migrations.AlterModelOptions(
            name='topic',
            options={'ordering': ('order',)},
        ),
        migrations.AlterModelOptions(
            name='uniquefile',
            options={'ordering': ('order',)},
        ),
    ]
