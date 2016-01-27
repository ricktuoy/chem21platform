# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('repo', '0043_auto_20160105_2057'),
    ]

    operations = [
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
        migrations.AlterUniqueTogether(
            name='authorsoffile',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='authorsoffile',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='authorsoffile',
            name='author',
        ),
        migrations.RemoveField(
            model_name='authorsoffile',
            name='file',
        ),
        migrations.AlterUniqueTogether(
            name='filesinquestion',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='filesinquestion',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='filesinquestion',
            name='file',
        ),
        migrations.RemoveField(
            model_name='filesinquestion',
            name='question',
        ),
        migrations.AlterUniqueTogether(
            name='lessonsinmodule',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='lessonsinmodule',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='lessonsinmodule',
            name='lesson',
        ),
        migrations.RemoveField(
            model_name='lessonsinmodule',
            name='module',
        ),
        migrations.AlterUniqueTogether(
            name='questionsinlesson',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='questionsinlesson',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='questionsinlesson',
            name='lesson',
        ),
        migrations.RemoveField(
            model_name='questionsinlesson',
            name='question',
        ),
        migrations.AlterModelOptions(
            name='module',
            options={'permissions': (('can_publish', 'Can publish modules'), ('change structure', 'Can change module structures'))},
        ),
        migrations.AlterField(
            model_name='uniquefile',
            name='ext',
            field=models.CharField(max_length=25, null=True),
        ),
        migrations.DeleteModel(
            name='AuthorsOfFile',
        ),
        migrations.DeleteModel(
            name='FilesInQuestion',
        ),
        migrations.DeleteModel(
            name='LessonsInModule',
        ),
        migrations.DeleteModel(
            name='QuestionsInLesson',
        ),
    ]
