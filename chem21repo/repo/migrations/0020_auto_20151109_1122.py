# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0019_auto_20151103_1454'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('title', models.CharField(
                    default=b'', max_length=100, blank=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LessonsInModule',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('lesson', models.ForeignKey(to='repo.Lesson')),
                ('module', models.ForeignKey(to='repo.Module')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PresentationsInQuestion',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('text', models.TextField(default=b'', blank=True)),
                ('pdf', models.ForeignKey(
                    related_name='pdf_question', to='repo.UniqueFile', null=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SlidesInPresentationVersion',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SourceFilesInPresentation',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('file', models.ForeignKey(to='repo.UniqueFile')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VideosInQuestion',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('file', models.ForeignKey(to='repo.UniqueFile')),
                ('question', models.ForeignKey(to='repo.Question')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='presentation',
            name='source_files',
        ),
        migrations.RemoveField(
            model_name='presentationversion',
            name='slides',
        ),
        migrations.AddField(
            model_name='presentation',
            name='source_files',
            field=models.ManyToManyField(
                to='repo.UniqueFile', through='repo.SourceFilesInPresentation'),
        ),
        migrations.AddField(
            model_name='presentationversion',
            name='slides',
            field=models.ManyToManyField(
                to='repo.PresentationSlide', through='repo.SlidesInPresentationVersion'),
        ),
        migrations.AddField(
            model_name='sourcefilesinpresentation',
            name='presentation',
            field=models.ForeignKey(to='repo.Presentation'),
        ),
        migrations.AddField(
            model_name='slidesinpresentationversion',
            name='presentation',
            field=models.ForeignKey(to='repo.PresentationVersion'),
        ),
        migrations.AddField(
            model_name='slidesinpresentationversion',
            name='slide',
            field=models.ForeignKey(to='repo.PresentationSlide'),
        ),
        migrations.AddField(
            model_name='question',
            name='presentations',
            field=models.ManyToManyField(
                to='repo.Presentation', null=True, through='repo.PresentationsInQuestion'),
        ),
        migrations.AddField(
            model_name='question',
            name='videos',
            field=models.ManyToManyField(
                to='repo.UniqueFile', through='repo.VideosInQuestion'),
        ),
        migrations.AddField(
            model_name='presentationsinquestion',
            name='presentation',
            field=models.ForeignKey(to='repo.Presentation'),
        ),
        migrations.AddField(
            model_name='presentationsinquestion',
            name='question',
            field=models.ForeignKey(to='repo.Question'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='modules',
            field=models.ManyToManyField(
                to='repo.Module', through='repo.LessonsInModule'),
        ),
    ]
