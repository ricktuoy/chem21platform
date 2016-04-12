# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0014_auto_20160407_1611'),
    ]

    operations = [
        migrations.CreateModel(
            name='learning template-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.learningtemplate',),
        ),
        migrations.CreateModel(
            name='molecule-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.molecule',),
        ),
        migrations.AddField(
            model_name='lesson',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='module',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='topic',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='template',
            field=models.ForeignKey(blank=True, to='repo.LearningTemplate', null=True),
        ),
        migrations.AlterField(
            model_name='module',
            name='template',
            field=models.ForeignKey(blank=True, to='repo.LearningTemplate', null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='template',
            field=models.ForeignKey(blank=True, to='repo.LearningTemplate', null=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='template',
            field=models.ForeignKey(blank=True, to='repo.LearningTemplate', null=True),
        ),
        migrations.AlterField(
            model_name='uniquefile',
            name='template',
            field=models.ForeignKey(blank=True, to='repo.LearningTemplate', null=True),
        ),
    ]
