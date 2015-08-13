# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import chem21repo.repo.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(unique=True, max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.AuthorUnicodeMixin),
        ),
        migrations.CreateModel(
            name='AuthorsOfFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('author', models.ForeignKey(related_name='files', to='repo.Author')),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateField(null=True)),
            ],
            bases=(models.Model, chem21repo.repo.models.EventUnicodeMixin),
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('path', models.CharField(unique=True, max_length=200)),
                ('title', models.CharField(max_length=200, null=True)),
                ('dir_level', models.IntegerField(default=0)),
                ('ready', models.BooleanField(default=False)),
                ('type', models.CharField(default=b'text', max_length=15, null=True)),
                ('size', models.IntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.PathUnicodeMixin),
        ),
        migrations.CreateModel(
            name='FileLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('destination', models.ForeignKey(related_name='filelink_origins', to='repo.File')),
                ('origin', models.ForeignKey(related_name='filelink_destinations', to='repo.File')),
            ],
        ),
        migrations.CreateModel(
            name='FileStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.ForeignKey(to='repo.File')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(unique=True, max_length=10)),
                ('working', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.NameUnicodeMixin),
        ),
        migrations.CreateModel(
            name='Path',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('active', models.BooleanField(default=True)),
                ('module', models.ForeignKey(related_name='paths', to='repo.Module', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.NameUnicodeMixin),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.NameUnicodeMixin),
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(unique=True, max_length=10)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.NameUnicodeMixin),
        ),
        migrations.AddField(
            model_name='path',
            name='topic',
            field=models.ForeignKey(related_name='paths', to='repo.Topic', null=True),
        ),
        migrations.AddField(
            model_name='module',
            name='topic',
            field=models.ForeignKey(related_name='modules', to='repo.Topic'),
        ),
        migrations.AddField(
            model_name='filestatus',
            name='status',
            field=models.ForeignKey(to='repo.Status'),
        ),
        migrations.AddField(
            model_name='filestatus',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='file',
            name='containing_path',
            field=models.ForeignKey(related_name='files', to='repo.Path', null=True),
        ),
        migrations.AddField(
            model_name='file',
            name='event',
            field=models.ForeignKey(to='repo.Event', null=True),
        ),
        migrations.AddField(
            model_name='file',
            name='status',
            field=models.ForeignKey(to='repo.Status', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='event',
            unique_together=set([('name', 'date')]),
        ),
        migrations.AlterIndexTogether(
            name='event',
            index_together=set([('name', 'date')]),
        ),
        migrations.AddField(
            model_name='authorsoffile',
            name='file',
            field=models.ForeignKey(related_name='authors', to='repo.File'),
        ),
        migrations.AlterUniqueTogether(
            name='filelink',
            unique_together=set([('origin', 'destination')]),
        ),
        migrations.AlterIndexTogether(
            name='filelink',
            index_together=set([('origin', 'destination')]),
        ),
        migrations.AlterUniqueTogether(
            name='authorsoffile',
            unique_together=set([('author', 'file')]),
        ),
        migrations.AlterIndexTogether(
            name='authorsoffile',
            index_together=set([('author', 'file')]),
        ),
    ]
