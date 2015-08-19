from django.contrib import admin
from .models import File, Topic, Module, Path, Author, Event, FileLink

# Register your models here.
admin.site.register(File)
admin.site.register(Topic)
admin.site.register(Module)
admin.site.register(Path)
admin.site.register(Author)
admin.site.register(Event)
admin.site.register(FileLink)