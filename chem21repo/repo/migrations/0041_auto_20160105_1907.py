# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0040_lesson_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='role',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='authors',
            field=models.ManyToManyField(to='repo.Author', through='repo.AuthorsOfFile'),
        ),
        migrations.AlterField(
            model_name='authorsoffile',
            name='author',
            field=models.ForeignKey(to='repo.Author'),
        ),
        migrations.AlterField(
            model_name='authorsoffile',
            name='file',
            field=models.ForeignKey(to='repo.UniqueFile'),
        ),
    ]
