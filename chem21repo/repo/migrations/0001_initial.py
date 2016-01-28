# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import filebrowser.fields
import chem21repo.repo.models
from django.conf import settings
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(unique=True, max_length=200)),
                ('role', models.CharField(max_length=200, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.AuthorUnicodeMixin),
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
                ('order_dirty', models.BooleanField(default=True)),
                ('path', models.CharField(unique=True, max_length=800)),
                ('title', models.CharField(max_length=200, null=True)),
                ('dir_level', models.IntegerField(default=0)),
                ('active', models.BooleanField(default=True)),
                ('ready', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['containing_path__topic', 'containing_path__module'],
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
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('dirty', models.TextField(default=b'[]')),
                ('title', models.CharField(default=b'', max_length=100, blank=True)),
                ('remote_id', models.IntegerField(null=True, db_index=True)),
                ('text', tinymce.models.HTMLField(default=b'', null=True, blank=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.TitleUnicodeMixin),
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('dirty', models.TextField(default=b'[]')),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(unique=True, max_length=10)),
                ('working', models.BooleanField(default=False)),
                ('remote_id', models.IntegerField(null=True, db_index=True)),
                ('text', tinymce.models.HTMLField(default=b'', null=True, blank=True)),
            ],
            options={
                'permissions': (('can_publish', 'Can publish modules'), ('change structure', 'Can change module structures')),
            },
            bases=(models.Model, chem21repo.repo.models.NameUnicodeMixin),
        ),
        migrations.CreateModel(
            name='Path',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=800)),
                ('active', models.BooleanField(default=True)),
                ('module', models.ForeignKey(related_name='paths', to='repo.Module', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.NameUnicodeMixin),
        ),
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
            name='PresentationsInQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('presentation', models.ForeignKey(to='repo.Presentation')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PresentationSlide',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('file', filebrowser.fields.FileBrowseField(max_length=500, null=True)),
                ('duration', models.IntegerField(help_text=b'Duration of this slide in milliseconds')),
                ('html', models.TextField()),
            ],
            options={
                'ordering': ('order',),
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
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('dirty', models.TextField(default=b'[]')),
                ('title', models.CharField(default=b'', max_length=100, blank=True)),
                ('text', tinymce.models.HTMLField(default=b'', null=True, blank=True)),
                ('byline', tinymce.models.HTMLField(default=b'', null=True, blank=True)),
                ('remote_id', models.IntegerField(null=True, db_index=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.TitleUnicodeMixin),
        ),
        migrations.CreateModel(
            name='SlidesInPresentationVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('presentation', models.ForeignKey(to='repo.PresentationVersion')),
                ('slide', models.ForeignKey(to='repo.PresentationSlide')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SourceFilesInPresentation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
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
            name='TextVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('text', models.TextField()),
                ('object_id', models.PositiveIntegerField(null=True, verbose_name=b'related object')),
                ('content_type', models.ForeignKey(verbose_name=b'content page', blank=True, to='contenttypes.ContentType', null=True)),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('dirty', models.TextField(default=b'[]')),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(unique=True, max_length=10)),
                ('remote_id', models.IntegerField(null=True, db_index=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
            bases=(models.Model, chem21repo.repo.models.NameUnicodeMixin),
        ),
        migrations.CreateModel(
            name='UniqueFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('dirty', models.TextField(default=b'[]')),
                ('checksum', models.CharField(max_length=100, unique=True, null=True)),
                ('path', models.CharField(max_length=255, null=True)),
                ('ext', models.CharField(max_length=25, null=True)),
                ('type', models.CharField(default=b'text', max_length=15, null=True)),
                ('title', models.CharField(max_length=200, null=True)),
                ('size', models.BigIntegerField(default=0)),
                ('file', filebrowser.fields.FileBrowseField(max_length=500, null=True)),
                ('cut_order', models.IntegerField(default=0)),
                ('ready', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=True)),
                ('s3d', models.BooleanField(default=False)),
                ('remote_path', models.CharField(max_length=255, null=True, blank=True)),
                ('remote_id', models.IntegerField(null=True, db_index=True)),
                ('authors', models.ManyToManyField(to='repo.Author', blank=True)),
                ('cut_of', models.ForeignKey(related_name='cuts', to='repo.UniqueFile', null=True)),
                ('event', models.ForeignKey(to='repo.Event', null=True)),
                ('status', models.ForeignKey(to='repo.Status', null=True)),
                ('version_of', models.ForeignKey(related_name='versions', to='repo.UniqueFile', null=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UniqueFilesofModule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('order_dirty', models.BooleanField(default=True)),
                ('file', models.ForeignKey(to='repo.UniqueFile')),
                ('module', models.ForeignKey(to='repo.Module')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='sourcefilesinpresentation',
            name='file',
            field=models.ForeignKey(to='repo.UniqueFile'),
        ),
        migrations.AddField(
            model_name='sourcefilesinpresentation',
            name='presentation',
            field=models.ForeignKey(to='repo.Presentation'),
        ),
        migrations.AddField(
            model_name='question',
            name='files',
            field=models.ManyToManyField(related_name='questions', to='repo.UniqueFile'),
        ),
        migrations.AddField(
            model_name='question',
            name='lessons',
            field=models.ManyToManyField(related_name='questions', to='repo.Lesson'),
        ),
        migrations.AddField(
            model_name='question',
            name='pdf',
            field=models.ForeignKey(related_name='pdf_question', to='repo.UniqueFile', null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='presentations',
            field=models.ManyToManyField(to='repo.Presentation', through='repo.PresentationsInQuestion'),
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
            field=models.ManyToManyField(to='repo.PresentationSlide', through='repo.SlidesInPresentationVersion'),
        ),
        migrations.AddField(
            model_name='presentationsinquestion',
            name='question',
            field=models.ForeignKey(to='repo.Question'),
        ),
        migrations.AddField(
            model_name='presentation',
            name='source_files',
            field=models.ManyToManyField(to='repo.UniqueFile', through='repo.SourceFilesInPresentation'),
        ),
        migrations.AddField(
            model_name='path',
            name='topic',
            field=models.ForeignKey(related_name='paths', to='repo.Topic', null=True),
        ),
        migrations.AddField(
            model_name='module',
            name='files',
            field=models.ManyToManyField(to='repo.UniqueFile', through='repo.UniqueFilesofModule'),
        ),
        migrations.AddField(
            model_name='module',
            name='topic',
            field=models.ForeignKey(related_name='modules', to='repo.Topic'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='modules',
            field=models.ManyToManyField(related_name='lessons', to='repo.Module'),
        ),
        migrations.AddField(
            model_name='filestatus',
            name='file',
            field=models.ForeignKey(to='repo.UniqueFile'),
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
        migrations.AlterUniqueTogether(
            name='event',
            unique_together=set([('name', 'date')]),
        ),
        migrations.AlterIndexTogether(
            name='event',
            index_together=set([('name', 'date')]),
        ),
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
            name='module-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.module',),
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
        migrations.AlterUniqueTogether(
            name='uniquefilesofmodule',
            unique_together=set([('file', 'module')]),
        ),
        migrations.AlterIndexTogether(
            name='uniquefilesofmodule',
            index_together=set([('file', 'module')]),
        ),
        migrations.AlterUniqueTogether(
            name='sourcefilesinpresentation',
            unique_together=set([('presentation', 'file')]),
        ),
        migrations.AlterIndexTogether(
            name='sourcefilesinpresentation',
            index_together=set([('presentation', 'file')]),
        ),
        migrations.AlterUniqueTogether(
            name='slidesinpresentationversion',
            unique_together=set([('presentation', 'slide')]),
        ),
        migrations.AlterIndexTogether(
            name='slidesinpresentationversion',
            index_together=set([('presentation', 'slide')]),
        ),
        migrations.AlterUniqueTogether(
            name='presentationsinquestion',
            unique_together=set([('question', 'presentation')]),
        ),
        migrations.AlterIndexTogether(
            name='presentationsinquestion',
            index_together=set([('question', 'presentation')]),
        ),
        migrations.AlterUniqueTogether(
            name='filelink',
            unique_together=set([('origin', 'destination')]),
        ),
        migrations.AlterIndexTogether(
            name='filelink',
            index_together=set([('origin', 'destination')]),
        ),
    ]
