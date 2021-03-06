# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0028_glossaryterm_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='containing_path',
        ),
        migrations.AlterUniqueTogether(
            name='filelink',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='filelink',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='filelink',
            name='destination',
        ),
        migrations.RemoveField(
            model_name='filelink',
            name='origin',
        ),
        migrations.RemoveField(
            model_name='filestatus',
            name='file',
        ),
        migrations.RemoveField(
            model_name='filestatus',
            name='status',
        ),
        migrations.RemoveField(
            model_name='filestatus',
            name='user',
        ),
        migrations.RemoveField(
            model_name='presentation',
            name='source_files',
        ),
        migrations.AlterUniqueTogether(
            name='presentationsinquestion',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='presentationsinquestion',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='presentationsinquestion',
            name='presentation',
        ),
        migrations.RemoveField(
            model_name='presentationsinquestion',
            name='question',
        ),
        migrations.RemoveField(
            model_name='presentationversion',
            name='audio',
        ),
        migrations.RemoveField(
            model_name='presentationversion',
            name='presentation',
        ),
        migrations.RemoveField(
            model_name='presentationversion',
            name='slides',
        ),
        migrations.AlterUniqueTogether(
            name='slidesinpresentationversion',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='slidesinpresentationversion',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='slidesinpresentationversion',
            name='presentation',
        ),
        migrations.RemoveField(
            model_name='slidesinpresentationversion',
            name='slide',
        ),
        migrations.AlterUniqueTogether(
            name='sourcefilesinpresentation',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='sourcefilesinpresentation',
            index_together=set([]),
        ),
        migrations.RemoveField(
            model_name='sourcefilesinpresentation',
            name='file',
        ),
        migrations.RemoveField(
            model_name='sourcefilesinpresentation',
            name='presentation',
        ),
        migrations.RemoveField(
            model_name='textversion',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='textversion',
            name='user',
        ),
        migrations.DeleteModel(
            name='event-power',
        ),
        migrations.DeleteModel(
            name='file link-power',
        ),
        migrations.RemoveField(
            model_name='question',
            name='presentations',
        ),
        migrations.RemoveField(
            model_name='uniquefile',
            name='cut_order',
        ),
        migrations.RemoveField(
            model_name='uniquefile',
            name='event',
        ),
        migrations.RemoveField(
            model_name='uniquefile',
            name='file',
        ),
        migrations.RemoveField(
            model_name='uniquefile',
            name='status',
        ),
        migrations.DeleteModel(
            name='File',
        ),
        migrations.DeleteModel(
            name='FileLink',
        ),
        migrations.DeleteModel(
            name='FileStatus',
        ),
        migrations.DeleteModel(
            name='Presentation',
        ),
        migrations.DeleteModel(
            name='PresentationsInQuestion',
        ),
        migrations.DeleteModel(
            name='PresentationSlide',
        ),
        migrations.DeleteModel(
            name='PresentationVersion',
        ),
        migrations.DeleteModel(
            name='SlidesInPresentationVersion',
        ),
        migrations.DeleteModel(
            name='SourceFilesInPresentation',
        ),
        migrations.DeleteModel(
            name='TextVersion',
        ),
    ]
