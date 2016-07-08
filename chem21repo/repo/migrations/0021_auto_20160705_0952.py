# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0020_auto_20160705_0939'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='topic',
            options={},
        ),
        migrations.AddField(
            model_name='lesson',
            name='attribution',
            field=models.ForeignKey(blank=True, to='repo.Author', null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='show_attribution',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='module',
            name='attribution',
            field=models.ForeignKey(blank=True, to='repo.Author', null=True),
        ),
        migrations.AddField(
            model_name='module',
            name='show_attribution',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='attribution',
            field=models.ForeignKey(blank=True, to='repo.Author', null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='show_attribution',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='topic',
            name='attribution',
            field=models.ForeignKey(blank=True, to='repo.Author', null=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='show_attribution',
            field=models.BooleanField(default=False),
        ),
    ]
