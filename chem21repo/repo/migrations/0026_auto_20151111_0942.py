# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0025_auto_20151110_1239'),
    ]

    operations = [
        migrations.CreateModel(
            name='FilesInQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=0)),
                ('working', models.BooleanField(default=True)),
                ('file', models.ForeignKey(to='repo.UniqueFile')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='videosinquestion',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='videosinquestion',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='videosinquestion',
            name='file',
        ),
        migrations.RemoveField(
            model_name='videosinquestion',
            name='question',
        ),
        migrations.RemoveField(
            model_name='question',
            name='videos',
        ),
        migrations.DeleteModel(
            name='VideosInQuestion',
        ),
        migrations.AddField(
            model_name='filesinquestion',
            name='question',
            field=models.ForeignKey(to='repo.Question'),
        ),
        migrations.AddField(
            model_name='question',
            name='files',
            field=models.ManyToManyField(to='repo.UniqueFile', through='repo.FilesInQuestion'),
        ),
        migrations.AlterUniqueTogether(
            name='filesinquestion',
            unique_together=set([('file', 'question')]),
        ),
        migrations.AlterIndexTogether(
            name='filesinquestion',
            index_together=set([('file', 'question')]),
        ),
    ]
