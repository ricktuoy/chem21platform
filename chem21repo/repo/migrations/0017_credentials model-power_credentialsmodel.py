# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import oauth2client.contrib.django_orm


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('repo', '0016_uniquefile_youtube_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='CredentialsModel',
            fields=[
                ('id', models.ForeignKey(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('credential', oauth2client.contrib.django_orm.CredentialsField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='credentials model-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.credentialsmodel',),
        ),
    ]
