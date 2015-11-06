from .models import Author
from .models import Event
from .models import FileLink
from .models import Module
from .models import Path
from .models import Topic
from .models import UniqueFile
from .models import UniqueFilesofModule
from django.contrib import admin

# Register your models here.
admin.site.register(UniqueFile)
admin.site.register(Topic)
admin.site.register(Module)
admin.site.register(Path)
admin.site.register(Author)
admin.site.register(Event)
admin.site.register(FileLink)

admin.site.register(UniqueFilesofModule)
