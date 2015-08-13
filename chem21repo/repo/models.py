from django.db import models

class BaseModel(Model):
	class Meta:
		abstract=True
	pass

def NameMixin(name_field):
	class _NameMixin(object):
		def __unicode__(self):
			return getattr(self,name_field)
	return _NameMixin

class OrderedMixin(object):
	order = models.IntegerField()

class Topic(OrderedMixin,NameMixin("name")):
	name = models.CharField(max_length=200)
	code = models.CharField(max_length=10,unique = True)

class Module(OrderedMixin,NameMixin("name")):
	name = models.CharField(max_length=200)
	code = models.CharField(max_length=10, unique = True)
	topic = models.ForeignKey(Topic, related_name='modules')
	working = models.BooleanField(default=False)
	def __unicode__(self):
		return "%s: %s" % (unicode(self.topic), self.name)

class Path(BaseModel, NameMixin("name")):
	name = models.CharField(max_length=200,unique=True)
	topic = models.ForeignKey(Topic,related_name='paths',null=True)
	module = models.ForeignKey(Module, related_name='paths',null=True)
	active = models.BooleanField(default=True)

class File(OrderedMixin,NameMixin("path")):
	path = models.CharField(max_length=200,unique = True)
	containing_path = models.ForeignKey(Path, related_name="files", null=True)
	dir_level = models.IntegerField(default=0)
	ready = models.BooleanField(default=False)
	type = models.CharField(max_length=15,default="text", null=True)
	size = models.IntegerField(default=0)
	status = models.CharField(default="raw")

class Status(BaseModel, NameMixin("name")):
	name = models.CharField(max_length=200)

class FileStatus(BaseModel):
	file =  models.ForeignKey(File)
	status = models.ForeignKey(Status)
	user = models.ForeignKey(User)