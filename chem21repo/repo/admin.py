from django.contrib import admin
from .models import Topic, Module, Path, Author, Event, FileLink, UniqueFile, UniqueFilesofModule

# Register your models here.
admin.site.register(UniqueFile)
admin.site.register(Topic)
admin.site.register(Module)
admin.site.register(Path)
admin.site.register(Author)
admin.site.register(Event)
admin.site.register(FileLink)

admin.site.register(UniqueFilesofModule)