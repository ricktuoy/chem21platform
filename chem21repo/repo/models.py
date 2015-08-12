from django.db import Model
from ordered_model import OrderedModel, OrderedRelationalModel

class BaseModel(Model):
	pass

def NameMixin(name_field):
	class _NameMixin(object):
		def __unicode__(self):
			return getattr(self,name_field)

	return _NameMixin

class Topic(OrderedModel,NameMixin("name")):
	name = CharField()
	code = CharField(unique = True)

class Module(OrderedModel,NameMixin("name")):
	name = CharField()
	code = CharField(unique = True)
	topic = ForeignKeyField(Topic, related_name='modules')
	working = BooleanField(default=False)
	def __unicode__(self):
		return "%s: %s" % (unicode(self.topic), self.name)

class Path(BaseModel, NameMixin("name")):
	name = CharField(unique=True)
	topic = ForeignKeyField(Topic,related_name='paths',null=True)
	module = ForeignKeyField(Module, related_name='paths',null=True)
	active = BooleanField(default=True)

class File(OrderedModel,NameMixin("path")):
	path = CharField(unique = True)
	containing_path = ForeignKeyField(Path, related_name="files", null=True)
	dir_level = IntegerField()
	ready = BooleanField(default=False)
	type = CharField(default="text", null=True)
	size = IntegerField(default=0)
	status = CharField(default="raw")

class Status(BaseModel, NameMixin("name")):
	name = CharField()

class FileStatus(BaseModel):
	file =  ForeignKeyField(File)
	status = ForeignKeyField(Status)
	user = ForeignKeyField(User)	

"""
class FilesInModule(OrderedModel):
	module = ForeignKeyField(Module, related_name = 'files')
	file = ForeignKeyField(File, related_name = 'modules')
	class Meta:
		primary_key = CompositeKey('module', 'file')
"""