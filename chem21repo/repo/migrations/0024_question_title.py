# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0023_question_lessons'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='title',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
    ]
