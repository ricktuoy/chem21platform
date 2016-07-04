# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0018_presentationaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='text',
            field=models.TextField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='module',
            name='text',
            field=models.TextField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='presentationaction',
            name='biblio',
            field=models.ForeignKey(blank=True, to='repo.Biblio', null=True),
        ),
        migrations.AlterField(
            model_name='presentationaction',
            name='image',
            field=models.ForeignKey(related_name='actions_of_image', blank=True, to='repo.UniqueFile', null=True),
        ),
        migrations.AlterField(
            model_name='presentationaction',
            name='text',
            field=models.TextField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='byline',
            field=models.TextField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='text',
            field=models.TextField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='text',
            field=models.TextField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='uniquefile',
            name='description',
            field=models.TextField(default=b'', null=True, blank=True),
        ),
    ]
