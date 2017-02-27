
from django.db import models
import json


class DrupalManager(models.Manager):
    def get_or_pull(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except self.model.DoesNotExist:
            instance = self.model(*args, **kwargs)
            instance.drupal.pull()
            instance.save()
            return instance


