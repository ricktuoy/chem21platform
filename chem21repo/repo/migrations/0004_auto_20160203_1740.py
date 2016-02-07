# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0003_textversion_published'),
    ]

    operations = [
        migrations.CreateModel(
            name='Biblio',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('citekey', models.CharField(max_length=300)),
                ('title', models.CharField(max_length=500)),
                ('display_string', models.CharField(max_length=1000)),
                ('inline_html', models.TextField(null=True, blank=True)),
                ('footnote_html', models.TextField(null=True, blank=True)),
                ('unknown', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='lesson',
            name='slug',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='module',
            name='slug',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='slug',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='slug',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
