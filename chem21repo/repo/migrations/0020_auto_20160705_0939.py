# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0019_auto_20160627_1140'),
    ]

    operations = [
        migrations.CreateModel(
            name='biblio-power',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('repo.biblio',),
        ),
        migrations.AlterField(
            model_name='presentationaction',
            name='action_type',
            field=models.CharField(default=b'F', max_length=1, choices=[(b'F', b'Footnote'), (b'I', b'Image'), (b'B', b'Biblio')], validators=[djchoices.choices.ChoicesValidator({b'I': b'Image', b'B': b'Biblio', b'F': b'Footnote'})]),
        ),
    ]
