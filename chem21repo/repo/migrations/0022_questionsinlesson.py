# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0021_auto_20151110_1015'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionsInLesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('lesson', models.ForeignKey(to='repo.Lesson')),
                ('question', models.ForeignKey(to='repo.Question')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
    ]
