from django.core.serializers.json import (
    Deserializer as StdDeserializer, Serializer
)

def Deserializer(stream_or_string, **options):
	for obj in StdDeserializer(stream_or_string, **options):
		obj.object.fixture_mode=True
		yield obj