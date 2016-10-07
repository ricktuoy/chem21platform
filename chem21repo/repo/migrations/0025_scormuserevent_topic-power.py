# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0024_remove_biblio_issn'),
    ]

    operations = [
        migrations.CreateModel(
            name='SCORMUserEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=10)),
                ('event', models.CharField(max_length=20)),
                ('datetime', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='topic-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.topic',),
        ),
    ]
