# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0044_auto_20160127_1241'),
    ]

    operations = [
        migrations.CreateModel(
            name='text version-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.textversion',),
        ),
        migrations.AddField(
            model_name='textversion',
            name='modified_time',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='textversion',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
