# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0017_credentials model-power_credentialsmodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='PresentationAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.IntegerField()),
                ('end', models.IntegerField()),
                ('text', tinymce.models.HTMLField(default=b'', null=True, blank=True)),
                ('action_type', models.CharField(max_length=1, choices=[(b'F', b'Footnote'), (b'I', b'Image'), (b'B', b'Biblio')], validators=[djchoices.choices.ChoicesValidator({b'I': b'Image', b'B': b'Biblio', b'F': b'Footnote'})])),
                ('biblio', models.ForeignKey(to='repo.Biblio', null=True)),
                ('image', models.ForeignKey(related_name='actions_of_image', to='repo.UniqueFile', null=True)),
                ('presentation', models.ForeignKey(related_name='actions', to='repo.UniqueFile')),
            ],
        ),
    ]
