from django.db import models
from django.contrib.auth.models import User
from filebrowser.fields import FileBrowseField

class BaseModel(models.Model):
	class Meta:
		abstract=True
	pass


def UnicodeMixinFactory(name_field):
	class _NameMixin(object):
		def __unicode__(self):
			try:
				return getattr(self,name_field)
			except TypeError:
				return " ".join([unicode(getattr(self, field)) for field in name_field])
	return _NameMixin


# needed for migration
NameUnicodeMixin = UnicodeMixinFactory("name")
NameUnicodeMixin.__name__ = "NameUnicodeMixin"
PathUnicodeMixin = UnicodeMixinFactory("path")
PathUnicodeMixin.__name__ = "PathUnicodeMixin"
TitleUnicodeMixin = UnicodeMixinFactory("title")
TitleUnicodeMixin.__name__ = "TitleUnicodeMixin"
AuthorUnicodeMixin = UnicodeMixinFactory("full_name")
AuthorUnicodeMixin.__name__ = "AuthorUnicodeMixin"
EventUnicodeMixin = UnicodeMixinFactory(("name","date"))
EventUnicodeMixin.__name__ = "EventUnicodeMixin"

class OrderedModel(BaseModel):
	order = models.IntegerField(default=0)
	class Meta:
		abstract=True

class Topic(OrderedModel,NameUnicodeMixin):
	name = models.CharField(max_length=200)
	code = models.CharField(max_length=10, unique = True)

class Module(OrderedModel,NameUnicodeMixin):
	name = models.CharField(max_length=200)
	code = models.CharField(max_length=10, unique = True)
	topic = models.ForeignKey(Topic, related_name='modules')
	working = models.BooleanField(default=False)
	def __unicode__(self):
		return "%s: %s" % (unicode(self.topic), self.name)

class Path(BaseModel,NameUnicodeMixin):
	name = models.CharField(max_length=800,unique=True)
	topic = models.ForeignKey(Topic,related_name='paths',null=True)
	module = models.ForeignKey(Module, related_name='paths',null=True)
	active = models.BooleanField(default=True)

class Status(BaseModel,NameUnicodeMixin):
	name = models.CharField(max_length=200)

class Author(BaseModel, AuthorUnicodeMixin):
	full_name = models.CharField(max_length=200,unique=True)

class Event(BaseModel, EventUnicodeMixin):
	name = models.CharField(max_length=100)
	date = models.DateField(null=True)
	@property
	def description(self):
		return self.name +": "+datetime.strftime(self.date,"%b %Y")
	class Meta:
		unique_together = (('name','date'),)
		index_together = (('name','date'),)

class UniqueFile(OrderedModel):
	checksum = models.CharField(max_length=100,null=True, unique=True)
	type = models.CharField(max_length=15,default="text", null=True)
	title = models.CharField(max_length=200,null=True)
	size = models.IntegerField(default=0)
	event = models.ForeignKey(Event, null=True)
	status = models.ForeignKey(Status,null=True)
	file = FileBrowseField(max_length=500,null=True)
	cut_of = models.ForeignKey('self',related_name='cuts',null=True)
	ready = models.BooleanField(default=False)
	active = models.BooleanField(default=True)
	

class File(OrderedModel, PathUnicodeMixin):
	path = models.CharField(max_length=800,unique = True)
	title = models.CharField(max_length=200,null=True)
	containing_path = models.ForeignKey(Path, related_name="files", null=True)
	dir_level = models.IntegerField(default=0)
	active = models.BooleanField(default=True)
	ready = models.BooleanField(default=False)
	def suggested_filename(self):
		_,ext = os.path.splitext(self.path)
		if self.event is not None:
			return slugify(self.event.name+" "+datetime.strftime(self.event.date,"%m %Y")+" "+self.title)+ext
		else:
			return slugify(" ".join([a.author.full_name for a in self.authors])+" "+self.title)+ext

	class Meta:
		ordering = [ 'containing_path__topic','containing_path__module' ]

class UniqueFilesofModule(BaseModel):
	file = models.ForeignKey(UniqueFile)
	module = models.ForeignKey(Module)
	class Meta:
		unique_together = ('file','module')
		index_together = ('file','module')


class FileLink(BaseModel):
	origin = models.ForeignKey(File, related_name="filelink_destinations")
	destination = models.ForeignKey(File, related_name="filelink_origins")
	class Meta:
		unique_together = ('origin','destination')
		index_together = ('origin','destination')

class AuthorsOfFile(OrderedModel):
	author = models.ForeignKey(Author,related_name='files')
	file = models.ForeignKey(UniqueFile,related_name='authors')
	class Meta:
		unique_together = ('author','file')
		index_together = ('author','file')

class FileStatus(BaseModel):
	file =  models.ForeignKey(UniqueFile)
	status = models.ForeignKey(Status)
	user = models.ForeignKey(User)



class Presentation(BaseModel):
	source_files = models.ManyToManyField(UniqueFile)
	

class PresentationSlide(OrderedModel):
	file = FileBrowseField(max_length=500,null=True)
	duration = models.IntegerField(help_text='Duration of this slide in milliseconds')
	html = models.TextField()

class PresentationVersion(BaseModel):
	presentation = models.ForeignKey(Presentation)
	version = models.IntegerField()
	slides = models.ManyToManyField(PresentationSlide)
	audio = models.ForeignKey(UniqueFile)


