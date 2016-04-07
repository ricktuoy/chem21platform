# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0013_uniquefile_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='LearningTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Molecule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, unique=True, null=True)),
                ('mol_def', models.TextField(default=b'', null=True, blank=True)),
                ('smiles_def', models.CharField(max_length=200, unique=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='thumbnail',
            field=models.ForeignKey(related_name='thumbnail_of', to='repo.UniqueFile', null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='template',
            field=models.ForeignKey(to='repo.LearningTemplate', null=True),
        ),
        migrations.AddField(
            model_name='module',
            name='template',
            field=models.ForeignKey(to='repo.LearningTemplate', null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='template',
            field=models.ForeignKey(to='repo.LearningTemplate', null=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='template',
            field=models.ForeignKey(to='repo.LearningTemplate', null=True),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='molecule',
            field=models.ForeignKey(related_name='related_files', to='repo.Molecule', null=True),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='template',
            field=models.ForeignKey(to='repo.LearningTemplate', null=True),
        ),
    ]
