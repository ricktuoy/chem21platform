# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0030_topic_remote_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='author-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.author',),
        ),
        migrations.CreateModel(
            name='event-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.event',),
        ),
        migrations.CreateModel(
            name='file link-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.filelink',),
        ),
        migrations.CreateModel(
            name='lesson-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.lesson',),
        ),
        migrations.CreateModel(
            name='question-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.question',),
        ),
        migrations.CreateModel(
            name='unique file-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.uniquefile',),
        ),
        migrations.CreateModel(
            name='unique filesof module-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.uniquefilesofmodule',),
        ),
        migrations.RemoveField(
            model_name='lesson', name="modules"),
        migrations.RemoveField(model_name='question', name='lessons'),
        migrations.AddField(
            model_name='lesson',
            name='modules',
            field=models.ManyToManyField(
                related_name='lessons', to='repo.Module'),
        ),
        migrations.AddField(
            model_name='question',
            name='lessons',
            field=models.ManyToManyField(
                related_name='questions', to='repo.Lesson'),
        ),
    ]
