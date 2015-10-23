# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import filebrowser.fields


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0005_auto_20151015_1458'),
    ]

    operations = [
        migrations.CreateModel(
            name='Presentation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PresentationSlide',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('duration', models.IntegerField(help_text=b'Duration of this slide in milliseconds')),
                ('html', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PresentationVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UniqueFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('checksum', models.CharField(max_length=100, unique=True, null=True)),
                ('type', models.CharField(default=b'text', max_length=15, null=True)),
                ('title', models.CharField(max_length=200, null=True)),
                ('size', models.IntegerField(default=0)),
                ('file', filebrowser.fields.FileBrowseField(max_length=500, null=True)),
                ('cut_of', models.ForeignKey(related_name='cuts', to='repo.UniqueFile', null=True)),
                ('event', models.ForeignKey(to='repo.Event', null=True)),
                ('status', models.ForeignKey(to='repo.Status', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UniqueFileofModule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.ForeignKey(to='repo.UniqueFile')),
                ('module', models.ForeignKey(to='repo.Module')),
            ],
        ),
        migrations.RemoveField(
            model_name='file',
            name='checksum',
        ),
        migrations.RemoveField(
            model_name='file',
            name='cut_of',
        ),
        migrations.RemoveField(
            model_name='file',
            name='event',
        ),
        migrations.RemoveField(
            model_name='file',
            name='file',
        ),
        migrations.RemoveField(
            model_name='file',
            name='size',
        ),
        migrations.RemoveField(
            model_name='file',
            name='status',
        ),
        migrations.RemoveField(
            model_name='file',
            name='type',
        ),
        migrations.AlterField(
            model_name='authorsoffile',
            name='file',
            field=models.ForeignKey(related_name='authors', to='repo.UniqueFile'),
        ),
        migrations.AlterField(
            model_name='filestatus',
            name='file',
            field=models.ForeignKey(to='repo.UniqueFile'),
        ),
        migrations.AddField(
            model_name='presentationversion',
            name='audio',
            field=models.ForeignKey(to='repo.UniqueFile'),
        ),
        migrations.AddField(
            model_name='presentationversion',
            name='presentation',
            field=models.ForeignKey(to='repo.Presentation'),
        ),
        migrations.AddField(
            model_name='presentationversion',
            name='slides',
            field=models.ManyToManyField(to='repo.PresentationSlide'),
        ),
        migrations.AddField(
            model_name='presentation',
            name='source_files',
            field=models.ManyToManyField(to='repo.UniqueFile'),
        ),
        migrations.AlterUniqueTogether(
            name='uniquefileofmodule',
            unique_together=set([('file', 'module')]),
        ),
        migrations.AlterIndexTogether(
            name='uniquefileofmodule',
            index_together=set([('file', 'module')]),
        ),
    ]
