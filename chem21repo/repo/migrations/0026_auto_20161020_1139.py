# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0025_scormuserevent_topic-power'),
    ]

    operations = [
        migrations.AddField(
            model_name='scormuserevent',
            name='course_id',
            field=models.CharField(default='greencpd-sss-topic-1', max_length=75),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='scormuserevent',
            unique_together=set([('username', 'event', 'course_id')]),
        ),
        migrations.AlterIndexTogether(
            name='scormuserevent',
            index_together=set([('username', 'course_id')]),
        ),
    ]
