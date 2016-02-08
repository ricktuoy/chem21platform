from django.core.serializers.json import (
    Deserializer as StdDeserializer, Serializer
)


def Deserializer(stream_or_string, **options):
    for obj in StdDeserializer(stream_or_string, **options):
        print "JSONF Deserialise"
        print obj.object.__class__
        obj.object.fixture_files_only = True
        obj.object.fixture_mode = True
        yield obj
