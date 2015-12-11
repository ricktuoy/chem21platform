# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0034_auto_20151208_1012'),
    ]

    operations = [
        migrations.AddField(
            model_name='authorsoffile',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='file',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='filesinquestion',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='lessonsinmodule',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='module',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='presentationsinquestion',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='presentationslide',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='question',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='questionsinlesson',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='slidesinpresentationversion',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='sourcefilesinpresentation',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='uniquefile',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='uniquefilesofmodule',
            name='order_dirty',
            field=models.BooleanField(default=True),
        ),
    ]
