# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0012_lesson_is_question'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquefile',
            name='description',
            field=tinymce.models.HTMLField(default=b'', null=True, blank=True),
        ),
    ]
