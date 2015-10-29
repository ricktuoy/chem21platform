from peewee import *
from django.utils.text import slugify
import argparse
import os, sys, errno, mimetypes
import json
import zipfile
import xml.etree.ElementTree as ET
import subprocess
import pprint
import sys
from datetime import datetime, date
from hurry.filesize import size
from playhouse.shortcuts import model_to_dict, dict_to_model
from playhouse.migrate import *
from PIL import Image
import hashlib
from boto.s3.connection import S3Connection

from moviepy.editor import VideoFileClip, concatenate_videoclips,ImageClip,AudioFileClip,CompositeVideoClip,vfx

DATABASE = 'cms.db'
AUDIO_ROOT = 'C:\Users\Public\Documents\Sound'
TEMP_VIDEO_ROOT = 'C:\Users\Public\Documents\TempVideo'
ROOT = 'Z:\CHEM21\Education and Training Material'
CAMREC_ROOT = 'Z:\RickTaylor\Camrec_for_filing'
NEW_VIDEO_RELPATH = 'New material\Recordings'
UNUSED_VIDEO_ROOT = 'Z:\RickTaylor\unused_video'
TEMP = 'C:\Users\\rick\Temp'
PPS_TO_SLIDES_EXEC = 'T:\Local CMS\ppt_to_mp4.exe'

MEDIASITE_ROOT = 'C:\Users\Public\Documents\Sustainable Chemistry Antwerp May 2015'
MEDIASITE_XML_FILE = 'MediaSitePresentation_60.xml'
MEDIASITE_SLIDE_FOLDER = 'Content'

PPS_TIMINGS_FILE = "Slides\SlideTimings.txt"

db=SqliteDatabase(DATABASE)

class InvalidCutError(Exception):
	pass

class CutParser(object):
	def __init__(self,str,video):
		try:
			cut,self.title=str.split("~",1)
		except ValueError:
			cut,self.title=str.split(None,1)
		except ValueError:
			raise InvalidCutError("Title badly formatted (use ~ or white space separator)")
		try:
			self.start,self.end = [self._parse_timestr(time) for time in cut.split("-")]
		except ValueError:
			raise InvalidCutError("Start/end times badly formatted (use - separator)")
		self.cut_video = self._apply(video) 
	def _parse_timestr(self,str):
		if not str:
			return None
		else:
			return tuple([int(el) for el in str.strip().split(":")])
	def _apply(self,video):
		print self.start, self.end
		return video.subclip(self.start,self.end)
	def filename(self):
		return slugify(self.title)+self.common_filename

	def write_file(self,path,common_filename="",fps=4,codec='mpeg4'):
		self.common_filename = common_filename
		source_path = os.path.join(TEMP_VIDEO_ROOT, self.filename())
		dest_path = os.path.join(path,self.filename())
		self.cut_video.write_videofile(source_path)
		try:
			os.remove(dest_path)
		except OSError:
			pass
		os.rename(source_path,dest_path)

class BaseModel(Model):
	class Meta:
		database = db

class OrderedModel(BaseModel):
	order = IntegerField(default=0)

def NameMixin(name_field):
	class _NameMixin(object):
		def __unicode__(self):
			try:
				return getattr(self,name_field)
			except TypeError:
				return " ".join([unicode(getattr(self, field)) for field in name_field])

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

class Author(BaseModel, NameMixin("full_name")):
	full_name = CharField(unique=True)

class Event(BaseModel, NameMixin(("name","date"))):
	name = CharField()
	date = DateField(null=True)
	@property
	def description(self):
		return self.name +": "+datetime.strftime(self.date,"%b %Y")
	class Meta:
		indexes = (
			(('name','date'),True) # unique key on name/date
		)

class UniqueFile(OrderedModel, NameMixin("checksum")):
	checksum = CharField(unique=True)
	cut_of = ForeignKeyField('self',related_name="cuts",null=True)
	ready = BooleanField(default=False)
	active = BooleanField(default=True)
	type = CharField(default="text", null=True)
	size = IntegerField(default=0)
	event = ForeignKeyField(Event, null=True)
	title = CharField(null=True)
	ext = CharField(null=True)
	path = CharField(null=True)
	s3d = BooleanField(default=False)
	def add_authors(self, authors):
		for author in authors:
			try:
				AuthorsOfFile.create(file=self, author=author)
			except IntegrityError:
				pass

	"""
	@property 
	def ext():
		_,ext = os.path.splitext(self.path)
		return ext
	@property
	def path():
		return self.instances[0].path
	"""

class File(OrderedModel,NameMixin("path")):
	path = CharField(unique = True)
	title = CharField(null=True)
	containing_path = ForeignKeyField(Path, related_name="files", null=True)
	dir_level = IntegerField(default=0)
	file_info = ForeignKeyField(UniqueFile, related_name="instances", null=True)
	active = BooleanField(default=True)

	@property
	def cut_of():
		return self.file_info.cut_of
	@property
	def ready():
		return self.file_info.ready
	@property
	def type():
		return self.file_info.type
	@property
	def size():
		return self.file_info.size
	@property
	def event():
		return self.file_info.event


	def suggested_filename(self):
		_,ext = os.path.splitext(self.path)
		if self.file_info.event is not None:
			return slugify(self.file_info.event.name+" "+datetime.strftime(self.file_info.event.date,"%m %Y")+" "+self.title)+ext
		else:
			return slugify(" ".join([a.author.full_name for a in self.file_info.authors])+" "+self.title)+ext





class UniqueFilesOfModule(BaseModel):
	file = ForeignKeyField(UniqueFile, related_name='modules')
	module = ForeignKeyField(Module, related_name='files')
	class Meta:
		indexes = (
			(('file','module'),True),
		)

class FileLink(BaseModel):
	origin = ForeignKeyField(File, related_name="filelink_destinations")
	destination = ForeignKeyField(File, related_name="filelink_origins")
	class Meta:
		indexes = (
			(('origin','destination'),True),
		)

class AuthorsOfFile(BaseModel):
	author = ForeignKeyField(Author,related_name='files')
	file = ForeignKeyField(UniqueFile,related_name='authors')
	class Meta:
		indexes = (
			(('author','unique_file'),True),
		)
#TODO migrate unique_file -> file

def generate_file_md5(path, blocksize=2**20):
    m = hashlib.md5()
    with open( path , "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()

def _get_s3_bucket():
	conn = S3Connection('AKIAIKJHTIHD6APQCPJA', '2MIQTd/UqD3QNQ85jVrvXpoPU/k4jmzeR11w0UG1')
	b = conn.get_bucket('chem21repo')
	return b
	
def push_file_to_s3(file, b=None):
	print "Pushing %s to AWS" % file.path
	if not b:
		b = _get_s3_bucket()
	if not file.s3d and file.active:
		if file.size > 199999999:
			print "Not pushing, file is large: %s" % file.path
			return False
		try:
			s3path = "media/sources/"+file.checksum+file.ext
		except TypeError:
			print "Bad checksum %s or ext %s" % (file.checksum, file.ext)
			return False
		k = b.get_key(s3path)
		if not k:
			k = b.new_key(s3path)
			k.set_contents_from_filename(_get_full_path(file.path))
		else:
			print "File exists at AWS"
			return False
		file.s3d = True
		file.save
		return True
	else:
		print "File inactive or already pushed"
		return False

def push_module_to_s3(module=None):
	if not module:
		module = Module.get(working=True)
	b = _get_s3_bucket()
	for file in module.files:
		push_file_to_s3(file.file,b)

def convert_large_files():
	vids = [v for v in UniqueFile.select().where(UniqueFile.size > 99999999, UniqueFile.type == "video")]
	for file in vids:
		vid = VideoFileClip(_get_full_path(file.path))
		basepath,_ = os.path.splitext(file.path)
		destpath = _get_full_path(basepath+".mp4")
		_, fname = os.path.split(destpath)
		temppath = os.path.join(TEMP_VIDEO_ROOT,fname)
		if not os.path.exists(destpath):
			vid.write_videofile(temppath)
			"""
			try:
			os.remove(destpath)
			except OSError:
			pass
			"""
			os.rename(temppath, destpath)
		new_file = store_file_details(destpath)
		for cut in file.cuts:
			cut.cut_of=new_file.file_info
			cut.save()
		result = push_file_to_s3(new_file.file_info)
		if result:
			file.active=False
			file.save
		if not result:
			print "Not pushed!"




			
def push_all_to_s3():
	for module in Module.select():
		print "Pushing all in %s " % module
		push_module_to_s3(module)

TABS = [Topic, Module, File, Path, Event, Author, UniqueFile, AuthorsOfFile, UniqueFilesOfModule]

def create_tables():
	db.connect()
	db.execute_sql('PRAGMA encoding = "UTF-16"')
	
	for tab in tabs:
		tab.drop_table(fail_silently=True)
		tab.create_table()

def _get_mediasite_root_xml(d):
	tree = ET.parse(os.path.join(d,MEDIASITE_XML_FILE))
	return tree.getroot()

def _get_mediasite_event(root,name=None):
	name = name or root.find('Properties').find('Folders').findall('Folder')[-1].find('Name').text

	dat = datetime.strptime(root.find('Properties').find('Presentation').find('CreationDate').text,"%Y-%m-%dT%H:%M:%S.%fZ")
	ev,created = Event.get_or_create(name=name,date=dat)
	return ev

def _get_mediasite_authors(root):
	for author in root.find('Properties').find('Presentation').find('Presenters').findall('PresentationPresenters'):
		au, created = Author.get_or_create(full_name="%s %s" % ( author.find('FirstName').text,author.find('LastName').text))
		return au

def _get_mediasite_title(root):
	return root.find('Properties').find('Presentation').find('Title').text

def _get_mediasite_duration(root):
	return root.find('Properties').find('Presentation').find('Duration').text

def _get_mediasite_slides(root):
	slides = root.find('Properties').find('SlideContent').find('Slides')
	return [slide for slide in slides.findall('Slide')]

def _get_cameravid_filename(root):
	return root.find('Properties').find('OnDemandContentList').find('PresentationContent').find('FileName').text

def _get_mediasite_slide_pairs(root):
	slides = _get_mediasite_slides(root)
	return zip(slides, slides[1:]+[None,])

def _get_mediasite_slide_image_path_from_number(d,num):
	return os.path.join(d,MEDIASITE_SLIDE_FOLDER,"slide_{:0>4d}_full.jpg".format(num))

def _get_pps_slide_image_path_from_number(d,num):
	src = os.path.join(d,"Slides","%d.png" % num)
	dest = os.path.join(d,"Slides","%d.jpg" % num)
	#if not os.path.exists(dest):
	im = Image.open(src)
	w,h = im.size
	ratio = float(w)/float(h)
	nw = int(float(1028) * float(w)/float(h))
	print h,w
	print nw
	im.resize((nw,1028), Image.ANTIALIAS).save(dest, quality=95)
	return dest.encode("ascii","ignore")

def _get_pps_audio_slide_from_number(d,num):
	src = os.path.join(d,"ppt","media","media%d.wav" % num)
	return AudioFileClip(src)

	
"""
def _get_imageclip_from_mediasite_slide(d,slide,next_slide,total_duration,show_duration):
	number = int(slide.find('Number').text)
	try:
		duration = int(next_slide.find('Time').text) - total_duration
	except AttributeError:
		duration = int(show_duration) - int(slide.find('Time').text)
	duration = int(round(duration/1000))
	return ImageClip(_get_mediasite_slide_image_path_from_number(d,number),duration=duration)
"""
def get_video_name_from_mediasite_dir(d):
	try:
		return slugify(" ".join(d.split(os.sep)[-2:]))+".mp4"
	except IndexError:
		return slugify(d.split(os.sep)[-1])+".mp4"

def get_imageclips_from_mediasite_dir(d):
	root = _get_mediasite_root_xml(d)
	show_duration = _get_mediasite_duration(root)
	total_duration = 0
	for slide,next_slide in _get_mediasite_slide_pairs(root):
		number = int(slide.find('Number').text)
		try:
			duration = int(round(int(next_slide.find('Time').text)/1000)) - total_duration
		except AttributeError:
			duration = int(show_duration) - int(slide.find('Time').text)
			duration = int(round(duration/1000))
		total_duration+=duration
		yield ImageClip(_get_mediasite_slide_image_path_from_number(d,number),duration=duration)

def _get_pps_timings(d):
	with open(os.path.join(d,PPS_TIMINGS_FILE)) as f:
		for line in f:
			x,y = line.split()
			yield (int(x), float(y))

def get_imageclips_from_pps_dir(d, narration=False):
	timings = _get_pps_timings(d)
	total_duration = 0
	for num,timing in timings:
		if narration:
			audio = _get_pps_audio_slide_from_number(d,num)
			duration = audio.duration
		else:
			duration = int(round(timing))
		#im = _get_pps_slide_image_path_from_number(d,num)
		#print im
		print duration

		clip = ImageClip(_get_pps_slide_image_path_from_number(d,num),duration=duration)
		if narration:
			clip = clip.set_audio(audio)
		yield clip

def remake_videoclip_from_pps_dir(f,d):
	vid = VideoFileClip(os.path.join(ROOT,f.path),audio=True)
	lst = [c for c in get_imageclips_from_pps_dir(d)]
	repvid = concatenate_videoclips(lst)
	repvid = repvid.set_audio(vid.audio)
	return repvid

def create_videoclip_from_pps(pps):
	dest = os.path.splitext(pps)[0]
	try:
		os.makedirs(os.path.join(dest,"Slides"))
	except OSError, e:
		if not e.errno == errno.EEXIST:
			raise e
	with zipfile.ZipFile(pps) as zf:
		zf.extractall(dest)
	pps = pps.encode('ascii','ignore')
	dest = dest.encode('ascii','ignore')
	print [PPS_TO_SLIDES_EXEC, pps, dest]
	subprocess.call([PPS_TO_SLIDES_EXEC,pps,dest])
	lst = [c for c in get_imageclips_from_pps_dir(dest, True)]
	return concatenate_videoclips(lst)
	

def get_videoclip_from_mediasite_dir(d):
	root = _get_mediasite_root_xml(d)
	camvid = VideoFileClip(os.path.join(d,MEDIASITE_SLIDE_FOLDER,_get_cameravid_filename(root)))
	vid = concatenate_videoclips([c for c in get_imageclips_from_mediasite_dir(d)])
	print "Total duration %d" % camvid.duration
	out = CompositeVideoClip([camvid,vid],size=vid.size)
	return out

def get_cmsfile_from_mediasite_dir(event_name,d,videopath):
	root = _get_mediasite_root_xml(d)
	title = _get_mediasite_title(root)
	authors = _get_mediasite_authors(root)
	event = _get_mediasite_event(root,event_name)
	cpath = _get_cmspath_for_file(videopath)
	if cpath is None:
		print "No path."
		return None,None
	root,basename = os.path.split(videopath)
	f = File(path=os.path.join(cpath.name,basename),title=title, event=event)
	print event
	#f.save()
	f.title,authors,f.event = _get_title_authors_event(f)
	f.containing_path = cpath
	f.type, f.size = _get_file_details(videopath)
	print "File details got. %s" % unicode(f)
	return f,authors

def _get_event(event):
	while True:
		event_name = default_input("Event title ('None' to skip event.)",getattr(event,'name',''))
		if event_name=="None":
			return None
		while True:
			try:
				date = event.date
				default_month = datetime.strftime(date, "%m")
				default_year = datetime.strftime(date, "%Y")
			except AttributeError:
				default_month=""
				default_year=""
			event_month = default_input("Event month (01=Jan)",default_month)
			event_year = default_input("Event year (e.g. 2015)",default_year)
			try:
				event_date = datetime.strptime("%s/%s" % (event_month,event_year), "%m/%Y")
			except ValueError:
				print "Month or year incorrectly formatted"
				continue
			break
		event,created = Event.get_or_create(name=event_name, date=event_date)
		if created:
			print "Created event %s" % event.description
		else:
			print "Found event %s" % event.description
		break
	return event

def _get_title_authors_event(f=None):
	default_title,ext = os.path.splitext(os.path.basename(f.path))
	default_title = slugify(default_title)
	title=default_input("Resource title",getattr(f,'title',default_title))
	print f
	event=_get_event(f.event)
	authors= set()
	try:
		default_authors = set([a.author.full_name for a in f.authors])
	except AttributeError:
		default_authors = set()
	i = 0
	while True:
		try:
			default_author = default_authors.pop()
		except KeyError:
			default_author = ""
		author = default_input("Author #%d; empty string to end." % i, default_author)
		if not author:
			break
		author,created = Author.create_or_get(full_name=author)
		authors.add(author)
		i+=1
	return (title,authors,event)

def alter_event(res):
	path = res.path
	full_path = os.path.join(ROOT,path)
	yn = yn_input("Show resource?")
	if yn=="Y":
		os.startfile(full_path)
	yn = yn_input("Change event?")
	if yn=="N":
		return
	res.event = _get_event()
	root,basename = os.path.split(path)
	res.path = os.path.join(root,res.suggested_filename())
	with db.atomic() as txn:
		res.save()
		print "Moving file %s to %s" % (full_path, os.path.join(ROOT,res.path))
		try:
			os.makedirs(os.path.join(ROOT,root))
		except OSError, e:
			if not e.errno == errno.EEXIST:
				raise e
		os.rename(full_path,os.path.join(ROOT,res.path))

def add_resource_details(res):
	path = res.path
	full_path = os.path.join(ROOT,path)
	yn = yn_input("Show resource?")
	if yn=="Y":
		os.startfile(full_path)
	res.title,authors,res.event = _get_title_authors_event()
	root,basename = os.path.split(path)
	res.path = os.path.join(root,res.suggested_filename())
	with db.atomic() as txn:
		res.save()
		for author in authors:
			AuthorsOfFile.create(author=author, file=res)
		print "Moving file %s to %s" % (full_path, os.path.join(ROOT,res.path))
		try:
			os.makedirs(os.path.join(ROOT,root))
		except OSError, e:
			if not e.errno == errno.EEXIST:
				raise e
		os.rename(full_path,os.path.join(ROOT,res.path))

def _get_cmspath_for_file(path=None):
	while True:
		code = raw_input("Module/topic code; enter \"*\" to preview and repeat.")
		if code =="*" and path is not None:
			print "Starting file now in your operating system."
			os.startfile(path)
			continue
		if code == "None":
			return None
		try:
			module = Module.get(Module.code == code)
			cpath = Path.get(Path.module == module, Path.active == True)
		except Module.DoesNotExist, Path.DoesNotExist:
			try:
				topic = Topic.get(Topic.code == code)
				cpath = Path.get(Path.topic == code, Path.module >> None, Path.active == True)
			except Topic.DoesNotExist, Path.DoesNotExist:
				print "Cannot find this module or topic code."
				continue
		break
	return cpath

def file_new_resource(path):
	root,rawfilename = os.path.split(path)
	filename,ext = os.path.splitext(rawfilename)
	print "Filing %s" % path
	cpath = _get_cmspath_for_file(path)
	type, size = _get_file_details(path)	
	dest_path = cpath.name
	title,authors,event = _get_title_authors_event()
	res = File(path=cpath.name,
		containing_path=cpath,  
		event=event, 
		title=title, 
		type=type, 
		size=size)
	if type=="video":
		res.path = os.path.join(res.path, NEW_VIDEO_RELPATH)
	res.path = os.path.join(res.path, rawfilename)
	with db.atomic() as txn:
		res.save()
		basename,_ = os.path.split(res.path)
		res.path = os.path.join(basename, res.suggested_filename())
		res.save()
		for author in authors:
			AuthorsOfFile.create(author=author, file=res)
		print "Moving file %s to %s" % (path, res.path)
		try:
			os.makedirs(os.path.join(ROOT,basename))
		except OSError, e:
			if not e.errno == errno.EEXIST:
				raise e
		os.rename(path,os.path.join(ROOT,res.path))

def get_ancestors(path,acc=[]):
	head,tail = os.path.split(path)
	print "%s __ %s" % (head,tail)
	if not head:
		if path:
			acc.insert(0,path)
		return acc
	acc.insert(0,path)
	return get_ancestors(head,acc)

def yn_input(question):
	yn=raw_input("%s (Y/N" % question)
	while yn not in ("Y","N"):
		yn = raw_input("Y or N please.")
	return yn

def default_input(question, default=None):
	if default is None:
		return raw_input(question)
	return raw_input("%s [%s]" % (question,default)) or default

def ask_for_code(cls,o):
	while True:
		try:
			o.code = raw_input("Enter code for %s (%s):" % (cls.__name__,o) )
			if not o.code:
				break
			o.save()
		except IntegrityError as e:
			print e			
			print "%s code '%s' exists" % (cls.__name__.capitalize(), o.code)
			obj = cls.get(code=o.code) 
			yn = yn_input("Should this folder be flagged as belonging to %s \"%s\"? (Y/N)" % (obj ,cls.__name__))
			while yn not in ("Y","N"):
				yn = raw_input("Y or N please.")
			if yn=="Y":
				o = obj
				break
			continue
		break
	return o
codes = None

def clear_path_cache(path_name):
	path = Path.delete().where(Path.name == path_name)

def guess_module(path, do_coding=True):
	ancs = get_ancestors(path,[])
	non_topics = set()
	non_modules = set()
	try:
		module_path, mcreated = Path.create_or_get(name=ancs[1])
	except IndexError as e:
		try:
			module_path, mcreated = Path.create_or_get(name=ancs[0])
		except IndexError:
			return None
		if not mcreated and module_path.topic:
			print "Top level topic folder %s" % path
			return module_path
	if not module_path.active:
		print "Module path %s flagged as inactive" % module_path
		return None
	try:
		module = Module.get(paths__name = module_path.name)
		print "Found existing module %s" % module
		return module_path
	except Module.DoesNotExist:
		topic_path, tcreated = Path.create_or_get(name=ancs[0])
		if not topic_path.active:
			print "Topic path %s flagged as inactive" % topic_path
			print "For topic %s" % topic_path.topic
			return None
		try:
			topic = Topic.get(paths__name = ancs[0])
		except Topic.DoesNotExist:
			topic = Topic(name = topic_path.name.capitalize())
			if do_coding:
				topic = ask_for_code(Topic,topic)
			if not topic.code:
				print "No topic code; saving topic path %s as inactive" % topic_path
				topic_path.active = False
				topic_path.save()
				return None
			topic.save()
		topic_path.topic = topic
		print "Saving topic %s; active is %s" % (topic_path, topic_path.active)
		topic_path.save()
		print topic
		if module_path.name == topic_path.name:
			#print "Top level topic folder"
			return topic_path
		module_path.topic = topic
		_ , component = os.path.split(module_path.name)
		try:
			module = Module.get(name=component)
			module.path = module_path
			module.topic = topic
		except Module.DoesNotExist:
			module = Module(path = module_path, topic=topic)
			print "Checking module path %s" % module_path.name
			print os.path.split(module_path.name)
			module.name = component.capitalize()
		if do_coding:
			module = ask_for_code(Module,module)
		if not module.code:
			if module_path.name!=topic_path.name:
				module_path.active = False
			module_path.save()
		try:
			module.save()
			print "Module saved."
		except IntegrityError as e:
			print e
			print "Module not saved %s." % module
			return None
	module_path.module = module
	module_path.save()
	return module_path

def _get_file_details(path):
	mimetype,_ = mimetypes.guess_type(path)
	try:
		type = mimetype.split("/")[0]
	except:
		type = None
	size = os.path.getsize(path)
	return (type, size)

def _win_decode(path):
	o = path
	try:
		o = o.decode('mbcs')
	except UnicodeDecodeError:
		try:
			o = o.decode('utf-16')
		except UnicodeDecodeError:
			print "Error decoding this filename: %s" % o
	return o

def _win_encode(path):
	o = path
	try:
		o = o.encode('mbcs')
	except UnicodeEncodeError:
		try:
			o = o.encode('utf-16')
		except UnicodeEncodeError:
			print "Error encoding this filename: %s" % o
	return o

def _get_rel_path(path):
	o = path.replace(ROOT+os.sep,'')
	o = o.replace(ROOT,'')
	return _win_decode(o)

def _get_full_path(path):
	return _win_decode(os.path.join(ROOT,path))

def transfer_many_relationships(frm, to):
	for cut in frm.cuts:
		cut.cut_of = to
		cut.save()
	to.add_authors([author.author for author in frm.authors])



def store_file_details(full_path, cut_parent=None, set_cut=lambda x,y:True,do_coding=False):
	root,name = os.path.split(full_path)
	containing_path = guess_module(_get_rel_path(root),do_coding=do_coding)
	level = _get_rel_path(root).count(os.sep)
	path = _get_rel_path(full_path)
	type,size = _get_file_details(full_path)
	print "Calculating checksum for %s" % _win_encode(path)
	checksum = generate_file_md5(full_path)
	pcdir, ext = os.path.splitext(full_path)
	defaults = {'size':size, 'type':type, 'path': path, 'ext': ext}
	if cut_parent:
		defaults['cut_of'] = cut_parent
	f_info, new_unique_file = UniqueFile.get_or_create(checksum=checksum, defaults = defaults)
	if f_info.active==False:
		print "This file has been flagged as inactive! %s" % path
	if new_unique_file and type=="video":
		title,authors,event = _get_title_authors_event(f_info)
		f_info.title = title
		f_info.event = event
		f_info.add_authors(authors)
	if type=="video" and os.path.exists(pcdir):
		set_cut(pcdir,f_info)
	if type=="video" and not (ext=="mp4" or ext==".mp4"):
		if not os.path.exists(pcdir+".mp4"):
			print "Generating mp4"
			convert_to_mp4(full_path)
		try:
			mp4file = File.get(path = _get_rel_path(pcdir+".mp4")).file_info
			print "Retrieved mp4 details."
		except File.DoesNotExist:
			print "mp4 file details not saved: saving"
			inp = default_input("Continue? (Y)es, (N)o - skip, (A)bort","Y")
			if inp=="A":
				sys.exit()
			if inp=="Y":
				mp4file = store_file_details(pcdir+".mp4",cut_parent,set_cut)
			else:
				mp4file = None
		if mp4file:
			print "Transferring file details to mp4 file, and deactivating this one. Continue?"
			inp = default_input("Continue? (Y)es, (N)o - skip, (A)bort","Y")
			if inp=="A":
				sys.exit()
			if inp=="Y":
				transfer_many_relationships(f_info, mp4file)
				mp4file.event = f_info.event
				mp4file.title = f_info.title 
				f_info.active = False
				mp4file.active = True
				mp4file.save()
	if not new_unique_file:
		f_info.size = size
		f_info.type = type
		f_info.ext = ext
		f_info.path = path
		if 'cut_of' in defaults:
			f_info.cut_of = defaults['cut_of']
	f_info.save()
	try: 
		UniqueFilesOfModule.create(module=containing_path.module, file=f_info)
	except IntegrityError:
		pass
	fl, new_path = File.get_or_create(path=path, defaults={'containing_path': containing_path, 'file_info':f_info})
	if not new_path:
		fl.containing_path = containing_path
		fl.file_info = f_info
		fl.save()
	return fl

def sync(do_coding=True, root_paths=(ROOT,)):
	def set_cut_gen(d):
		def set_cut(path,finfo):
			d[path] = finfo
		return set_cut
	for root_path in paths:
		cut_vid_paths = {}
		set_cut = set_cut_gen(cut_vid_paths)
		for root, dirs, files in os.walk(root_path):
			for name in files:
				full_path = _win_encode(os.path.join(root, name))
				print "Found %s " % full_path
				store_file_details(full_path, cut_parent=cut_vid_paths.get(root,None),set_cut=set_cut)
				


def prune_dead_paths():
	for path in Path.select().where(Path.active==True):
		full_path = _get_full_path(path.name)
		print full_path
		if not os.path.exists(full_path):
			path.active=False
			path.save()
	for file in File.select().where(File.active==True):
		full_path = _get_full_path(file.path)
		try:
			full_path = full_path.encode('mbcs')
		except UnicodeEncodeError:
			try:
				full_path = full_path.decode('utf-16')
			except UnicodeDecodeError:
				print "Error decoding this filename: %s" % path
		if not os.path.exists(full_path):
			print "Dead file: %s" % full_path
			file.active=False
			file.file_info=None
			file.save()
	prune_dead_unique_files()

def prune_dead_unique_files():
	for finfo in UniqueFile.select():
		try:
			inst = finfo.instances[0]
		except IndexError:
			finfo.active = False
			finfo.save()

def _get_file_path_from_id(id):
	return File.get(id=id).path


def cut_video(path,filestream=sys.stdin):
	video = VideoFileClip(path)
	folder_path, ext = os.path.splitext(path)
	try:
		os.makedirs(folder_path)
	except OSError, e:
		if not e.errno == errno.EEXIST:
			raise e
	while True:
		cutstr = filestream.readline()
		try:
			cut = CutParser(cutstr, video)
		except InvalidCutError, e:
			print "EOF (%s)" % e
			break
		cut.write_file(folder_path,".mp4")
		full_path = os.path.join(folder_path, cut.filename())
		containing_path = guess_module(_get_rel_path(folder_path),do_coding=False)
		vid_file = File.get(path=_get_rel_path(path))
		path = _get_rel_path(full_path)
		type,size = _get_file_details(full_path)
		checksum = generate_file_md5(full_path)
		defaults = {'size':size, 'type':type,'cut_of':vid_file.file_info}
		f_info, info_created = UniqueFile.get_or_create(checksum=checksum, defaults=defaults)
		if not info_created:
			f_info.cut_of = defaults['cut_of']
			f_info.size = defaults['size']
			f_info.type = defaults['type']
			f_info.save()
		fl, created = File.get_or_create(path = path, defaults = {'containing_path':containing_path, 'active':True,'file_info':f_info})
		if not created: 
			fl.file_info = f_info
			fl.active = True
			fl.containing_path = containing_path
			fl.save()

def concat_video(paths, outpath):
	clips = [VideoFileClip(path) for path in paths]
	# find dimensions of largest clip for our viewport
	tx = max([clip.size[0] for clip in clips])
	ty = max([clip.size[1] for clip in clips])
	# centre all clips in the viewport
	def margin(cx,cy):
		dx = tx- cx
		dy = ty - cy
		mx1 = int(dx/2)
		mx2 = dx - mx1
		my1 = int(dy/2)
		my2 = dy - my1
		return {'left':mx1,'right':mx2,'top':my1,'bottom':my2}
	clips = [clip.fx( vfx.margin,**margin(*clip.size)) for clip in clips] 
	# stick them together
	final_clip = concatenate_videoclips(clips)
	final_clip.write_videofile(outpath,fps=24,)

def concat_audio(paths, outpath):
	clips = [AudioFileClip(path) for path in paths]
	final_cl

def _list_query(topic):
	files = File.select(File,Path,UniqueFile).join(Path).join(UniqueFile, on=File.file_info).where(Path.active == True,File.active == True).order_by(Path.topic, Path.module)
	working = get_working_module()
	if working:
		files = files.where(Path.module == working)
	if topic:
		files = files.where(Path.topic == topic)
	return files

def _list_videos_query(topic=None):
	files = _list_query(topic)
	files = files.where(UniqueFile.type=="video", UniqueFile.active==True)
	return files

def _list_videos_no_cuts_query(topic=None):
	files = _list_videos_query(topic)
	files = files.where(UniqueFile.cut_of==None)
	return files

def _list_cuts_of_video(video_id,topic=None):
	files = _list_videos_query(topic)
	file_info = UniqueFile.select(UniqueFile.id).join(File).where(File.id==video_id)
	try:
		files = files.where(UniqueFile.cut_of==file_info[0].id)
	except IndexError:
		files = []
	return files

def _list_audio_query(topic=None):
	files = _list_query(topic)
	files = files.where(UniqueFile.type=="audio")
	return files

def _list_apps_query(topic=None):
	files = _list_query(topic)
	files = files.where(UniqueFile.type=="application")
	return files

def _list_events_query():
	events = Event.select()
	return events


def _list_authors_query():
	authors = Author.select()
	return authors

def _list_no_details_query():
	files = _list_videos_query(None)
	files = files.where(File.title >> None)
	return files


def list(topic=None, query=None):
	if query is None:
		files = _list_query(topic)
	else:
		files = query
	ctopic=None
	cmodule=None
	for f in files:
		out=""
		if ctopic != f.containing_path.topic:
			out += unicode(f.containing_path.topic) +"\n"
			ctopic = f.containing_path.topic
		if cmodule != f.containing_path.module:
			out += "-- %s" % unicode(f.containing_path.module)+"\n"
			cmodule = f.containing_path.module
		if f.path != f.containing_path.name:
			yield "%s---- %s" % (out, f.path.replace(f.containing_path.name,''))

def list_videos(topic=None,cuts_of=None):
	if cuts_of:
		files = _list_cuts_of_video(topic=topic,video_id=cuts_of)
	else:
		files = _list_videos_no_cuts_query(topic=topic)
	total = 0
	for f in files:
		yield "%d: %s %s" % (f.id,f.path,size(f.file_info.size))
		total += f.file_info.size
	yield size(total)

def list_audio(topic=None):
	files = _list_audio_query()
	total = 0
	for f in files:
		yield "%d: %s %s" % (f.id,f.path,size(f.size))
		total += f.size
	yield size(total)

def list_applications(topic=None):
	files = _list_apps_query()
	total = 0
	for f in files:
		yield "%d: %s %s" % (f.id,f.path,size(f.size))
		total += f.size
	yield size(total)

def list_videos_by_event():
	files = _list_videos_query().order_by(File.event)
	cevent = None
	for f in files:
		if f.event is not None:
			out=""
			if cevent != f.event:
				out+="\n\n"+f.event.description+"\n"
				cevent=f.event
			yield "%s-- %s" % (out, f.path)

def list_authors():
	for a in _list_authors_query():
		yield "%s" % a.full_name

def list_events():
	for e in _list_events_query():
		yield "%s" % e.description

def rip_audio(f):
	clip = VideoFileClip(os.path.join(ROOT,f.path),audio=True)
	clip.audio.set_duration(clip.duration).to_audiofile(os.path.join(AUDIO_ROOT,str(f.id)+".mp3"))

def update_audio(vidf,audp=None):
	if not audp:
		audp = os.path.join(AUDIO_ROOT,str(vidf.id)+".mp3")
	else:
		audp = os.path.join(ROOT,audp.path)
	videopath = os.path.join(ROOT,vidf.path)
	clip = VideoFileClip(videopath,audio=True)
	audio = AudioFileClip(audp)
	clip= clip.set_audio(audio)
	clip.write_videofile(videopath)

def batch_rip_audio(topic=None):
	for f in _list_videos_query():
		rip_audio(f)
		
def get_working_module():
	try:
		return Module.get(Module.working == True)
	except Module.DoesNotExist:
		return None

def workon(module):
	with db.atomic() as txn:
		query = Module.update(working=False)
		query.execute()
		if module is not None:
			query = Module.update(working=True).where(Module.code==module)
			if not query.execute():
				txn.rollback()
				print "Module (%s) not found." % (module)
	print "Working module is %s" % get_working_module()

def load(codes):
	for name,path in codes.iteritems():
		pdata = {'active':True, 'name': name}
		ancs = get_ancestors(name)
		#print name,path 
		try:
			pdata['topic'],created = Topic.create_or_get(code=path['topic'],name=path['name'])
			if not created and 'module' not in path:
				pdata['topic'].name = path['name']
				pdata['topic'].save()
				print "Saved topic name %s" % pdata['topic'].name
		except KeyError:
			pass
		try:
			pdata['module'],created = Module.create_or_get(code=path['module'],name=path['name'],topic=pdata['topic'])
		except KeyError as e:
			pass
		try:
			Path.create(**pdata)
		except IntegrityError:
			print "Path %s exists in DB" % name

def dedup_events():
	events = {}
	for event in Event.select():
		event_key = tuple(model_to_dict(event,only=[Event.name,Event.date]).items())
		try:
			events[event_key].add(event.id)
		except KeyError:
			events[event_key] = set([event.id])
	print events
	for key, eids in events.iteritems():
		with db.atomic() as txn:
			keep_id=eids.pop()
			print keep_id
			query = UniqueFile.update(event=keep_id).where(UniqueFile.event << [e for e in eids])
			done = query.execute()			
			query = Event.delete().where(Event.id << [e for e in eids])
			done = query.execute()
			if done != len(eids):
				txn.rollback()
				raise Exception("Unexpected delete count: %d v %d" % (done, len(eids)))


def dedup_author_files():
	authorfiles = {}
	for authorfile in AuthorsOfFile.select():
		author_key = tuple(model_to_dict(authorfile,recurse=False,only=[AuthorsOfFile.author,AuthorsOfFile.file]).items())
		try:
			authorfiles[author_key].add(authorfile.id)
		except KeyError:
			authorfiles[author_key] = set([authorfile.id])
	for key,afids in authorfiles.iteritems():
		keep_id = afids.pop()
		query = AuthorsOfFile.delete().where(AuthorsOfFile.id << [af for af in afids])
		done = query.execute()

def dedup_author_unique_files():
	authorfiles = {}
	for authorfile in AuthorsOfFile.select():
		author_key = tuple(model_to_dict(authorfile,recurse=False,only=[AuthorsOfFile.author,AuthorsOfFile.unique_file]).items())
		try:
			authorfiles[author_key].add(authorfile.id)
		except KeyError:
			authorfiles[author_key] = set([authorfile.id])
	for key,afids in authorfiles.iteritems():
		keep_id = afids.pop()
		query = AuthorsOfFile.delete().where(AuthorsOfFile.id << [af for af in afids])
		done = query.execute()

def populate_unique_file_cut_keys():
	for finfo in UniqueFile.select():
		files = [fl for fl in finfo.instances]
		fnames = [fl.title for fl in files]
		print files
		try:
			finfo.cut_of = files[0].cut_of.file_info
			print "Saving cut parent to be %s" % files[0].cut_of.file_info
		except AttributeError:
			pass
		except IndexError:
			print "No instances of this file info!"
			print finfo
"""
def fix_cut_keys():
	for finfo in UniqueFile.select().active=False):
		pk = finfo.cut_of.id
		print pk
	raise Exception("BPOOP")
"""
def populate_unique_files_of_module():
	for finfo in UniqueFile.select():
		for file in finfo.instances:
			try:
				UniqueFilesOfModule.create(file=finfo, module=file.containing_path.module)
				print "Success: %s" % file.path
			except Exception as e:
				print "Fail: %s" % e

def populate_unique_file_titles():
	for f in File.select().where(File.active==True):
		try:
			fi = f.file_info
			filename,ext = os.path.splitext(os.path.basename(f.path))
			if f.title:
				fi.title = f.title
			else:
				fi.title = filename
			fi.path = f.path
			fi.ext = ext
			#print fi.path
			#print fi.ext
			fi.save()
			print "Done"
		except AttributeError as e:
			print e
			print "No file info: %s" % f
	raise Exception("FUMMF")

			

SCHEMA_FILE = '.schema_index'

def get_schema_index():
	try:
		with open(SCHEMA_FILE,'r') as f:
			i= int(f.read())
			return i
	except EnvironmentError:
		return 0

def set_schema_index(i):
	with open(SCHEMA_FILE,'w') as f:
		f.write(str(i))

def populate_unique_file():
	#UniqueFile.delete().execute()
	files = File.select().where(File.active==True)


	get_defaults = lambda file: {
			'cut_of':file.cut_of,
			'ready':file.ready,
			'type':file.type,
			'size':file.size,
			'event':file.event
		} 
	pp = pprint.PrettyPrinter(indent=4)
	files = [f for f in files]
	for file in files:
		try:
			module = file.containing_path.module
		except AttributeError:
			module = None
		defaults = get_defaults(file)
		if not file.checksum:
			full_path = os.path.join(ROOT, file.path)	
			checksum = generate_file_md5(full_path)
		else:
			checksum = file.checksum
		unique_file, created = UniqueFile.get_or_create(checksum = checksum, defaults = defaults)
		if not created:
			#	paths = [file.path for file in unique_file.instances]
			#	print "File with checksum %s exists at paths %s" % (file.checksum, ", ".join(paths))
			if get_defaults(unique_file) != defaults:
				print "y) Existing file info%s****%s%s" % (os.linesep, os.linesep, pp.pformat(get_defaults(unique_file)))
				print "n) New file info%s****%s%s" % (os.linesep, os.linesep, pp.pformat(defaults))
				yn = yn_input("Keep existing file info? (n= use new file info)")
				if yn=="N":
					unique_file.cut_of = file.cut_of
					unique_file.ready = file.ready
					unique_file.type = file.type
					unique_file.event = file.event
					unique_file.save()
			else:
				print "It has identical file info."
		else:
			print "Created new unique file"
		file.file_info = unique_file
		file.save()

def populate_unique_file_keys():
	for file in File.select().where(File.active==True):
		unique_file = UniqueFile.get(checksum = file.checksum)
		for author in file.old_authors:
			author.unique_file = unique_file
			author.save()



def do_migrate():
	migrator = SqliteMigrator(db)
	migrations = [
		{	'premigrate':dedup_events,
			'migrate':[migrator.add_index('event', ('name','date'), True),]
		},
		{	'premigrate':FileLink.create_table,
		},
		{	'premigrate':dedup_author_files,
			'migrate':[migrator.add_index('authorsoffile', ('author_id','file_id'), True),]	
		},
		{
			'migrate':[migrator.add_column('file', 'cut_of', ForeignKeyField(rel_model=File, to_field=File.id, null=True))]
		},
		{
			'migrate':[ migrator.drop_column('file', 'cut_of'),
						migrator.add_column('file', 'cut_of_id', ForeignKeyField(rel_model=File, to_field=File.id, null=True))
			]

		},
		{
			'migrate':[ migrator.add_column('file', 'active', BooleanField(default=True)),
			]

		},
		{
			'migrate':[ migrator.add_column('file', 'checksum', CharField(null=True)),
			]
		},
		{
			'migrate':[ migrator.add_column('authorsoffile', 'unique_file_id', ForeignKeyField(rel_model=UniqueFile, to_field=UniqueFile.id, null=True)),
						migrator.add_column('file','file_info_id', ForeignKeyField(rel_model=UniqueFile, to_field=UniqueFile.id, null=True)) ],
			'postmigrate': [populate_unique_file_keys, dedup_author_unique_files]
		},
		{
			'migrate': [migrator.drop_column('uniquefile','active')]
		},
		{	'premigrate':[populate_unique_file_cut_keys,]
		},
		{
			'premigrate':[populate_unique_files_of_module,]
		},
		{
			'premigrate':[populate_unique_files_of_module,]
		},
				{
			'premigrate':[populate_unique_files_of_module,]
		},
		{
			'migrate': [ migrator.add_column('uniquefile','title',CharField(null=True)), ],
			'postmigrate': populate_unique_file_titles

		},
		{
			'migrate': [migrator.add_column('uniquefile','active',BooleanField(default=True)),],

		},
		{
			'premigrate': [prune_dead_unique_files, populate_unique_file_titles,]

		},
		{
			'migrate': [migrator.drop_column('file','cut_of_id'),
			migrator.drop_column('file','ready'),
			migrator.drop_column('file','type'),
			migrator.drop_column('file','size'),
			migrator.drop_column('file','event_id'),
			]
		},
		{
			'migrate': [migrator.drop_column('file','checksum'),]
		},
		{
			'migrate':[migrator.add_index('event', ('name','date'), True),]
		},
		{
			'migrate':[migrator.drop_column('authorsoffile','file_id'),
					migrator.rename_column('authorsoffile','unique_file_id','file_id')]
		},
		{
			'migrate': [migrator.add_column('uniquefile','path',CharField(null=True)),
						migrator.add_column('uniquefile','ext',CharField(null=True))],
			'postmigrate':[populate_unique_file_titles,]
		},
		{
			'migrate': [migrator.add_column('uniquefile','s3d',BooleanField(default=0)),]
		},
		{
			'migrate': [migrator.add_column('uniquefile','file',CharField(null=True)),]
		},
		{
			'premigrate': [push_all_to_s3,]
		},
		{
			'premigrate': [convert_large_files,]
		}

	]
	migrate_index = get_schema_index()
	print "Current schema index: %s" % migrate_index
	print "Current number of migrations: %s" % len(migrations)
	if migrate_index < len(migrations):
		for m in migrations[migrate_index:]:
			print "Running migration %d" % migrate_index
			if 'premigrate' in m:
				try:
					m['premigrate']()
				except TypeError:
					for pm in m['premigrate']:
						print "Running submigration"
						pm()
			if 'migrate' in m:
				migs = m['migrate']
				try:
					migrate(*migs)
				except OperationalError as e:
					print e
				"""
				except Exception as e:
					print "Error caught - setting schema index to %d" % migrate_index
					set_schema_index(migrate_index)
					raise e
				"""
			if 'postmigrate' in m:
				try:
					m['postmigrate']()
				except TypeError:
					for pm in m['postmigrate']:
						pm()
			migrate_index+=1
	set_schema_index(migrate_index)

def dump_codes():
	query = Path.select(Path.name, Path.module, Path.topic).join(Module, JOIN_LEFT_OUTER).join(Topic, JOIN_LEFT_OUTER).where(Path.active==True)
	ret = {}
	for path in query:
		#print path
		code = {}
		try:
			code['module'] = path.module.code
			code['name'] = path.module.name
		except AttributeError:
			pass
		try:
			code['topic'] = path.topic.code
			if 'name' not in code:
				code['name'] = path.topic.name
		except AttributeError:
			pass
		if code:
			ret[path.name] = code
	ret = {'paths':ret}
	authors = [model_to_dict(author) for author in Author.select()]
	events = [model_to_dict(event) for event in Event.select()]
	return ret

def struct():
	query = Path.select(Path.module, Path.topic).join(Module, JOIN_LEFT_OUTER).join(Topic, JOIN_LEFT_OUTER).distinct().order_by(Path.topic,Path.module)
	for path in query:
		if path.module:
			yield "-- %s %s" % (path.module.code, unicode(path.module.name))
		elif path.topic:
			yield "%s %s" % (path.topic.code, unicode(path.topic))
		else:
			continue

class DateTimeEncoder(json.JSONEncoder):
		def default(self, obj):
			if isinstance(obj, date):
				return obj.isoformat()
			# Let the base class default method raise the TypeError
			return json.JSONEncoder.default(self, obj)

def make_django_fixture(app_name):
	fix=[]
	for t in TABS:
		if t.__name__.lower() in ("file","path"):
			continue
		model_name = "%s.%s" % (app_name, t.__name__.lower())
		for instance in t.select():
			fields = model_to_dict(instance, recurse=False, exclude=[getattr(t,'id'),])
			fix.append({'model':model_name, 'pk':instance.id, 'fields':fields})

	date_handler = lambda obj: (
    	obj.isoformat()
    	if isinstance(obj, datetime)
#    	or isinstance(obj, date)
    	else obj
	)
	print json.dumps(fix, cls = DateTimeEncoder)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help = 'Function: init, sync, list', dest='mode')

init_parser = subparsers.add_parser('init', help="Intialise DB")

sync_parser = subparsers.add_parser('sync', help="Sync DB to file root")
sync_parser.add_argument('-c', help='Code unknown paths', dest='do_coding', action='store_true')
sync_parser.add_argument('-a', help='Sync entire file tree', dest='do_all', action='store_true')
sync_parser.set_defaults(do_coding=False, do_all=False)

clear_path_parser = subparsers.add_parser('clear_path', help="Clear path from cache")
clear_path_parser.add_argument('path_name',help='Path to clear')


list_parser = subparsers.add_parser('list', help="List managed files by topic and module")
list_parser.add_argument('-v', dest='type', action='store_const', const='video')
list_parser.add_argument('-V', dest='type', action='store_const', const='video_by_event')
list_parser.add_argument('-n', dest='type', action='store_const', const='no_details')
list_parser.add_argument('-e', dest='type', action='store_const', const='events')
list_parser.add_argument('-a', dest='type', action='store_const', const='authors')
list_parser.add_argument('-A', dest='type', action='store_const', const='applications')
list_parser.add_argument('-s', dest='type', action='store_const', const='sound')
list_parser.add_argument('-C', dest='cut_of')
list_parser.set_defaults(cut_of=None)

list_alter_parser = subparsers.add_parser('list_events_to_alter', help="List managed files to alter")

workon_parser = subparsers.add_parser('workon', help="Set working topic and module")
workon_parser.add_argument('module',help='Unique module code')

deactivate_parser = subparsers.add_parser('deactivate', help="Cancel current working module")

dump_parser = subparsers.add_parser('dump', help="Dump manually entered data")

load_parser = subparsers.add_parser('load', help="Load manually entered data")

rebuild_parser = subparsers.add_parser('rebuild', help="Rebuild database")
rebuild_parser.add_argument('--code', help='Code unknown paths', dest='do_coding', action='store_true')
rebuild_parser.set_defaults(do_coding=False)

build_parser = subparsers.add_parser('build', help="Build database")
build_parser.add_argument('--code', help='Code unknown paths', dest='do_coding', action='store_true')
build_parser.set_defaults(do_coding=False)

struct_parser = subparsers.add_parser('struct', help="Show structure")

rename_parser = subparsers.add_parser('rename', help="Rename object")
rename_parser.add_argument('-m', dest='module')
rename_parser.add_argument('-t', dest='topic')
rename_parser.add_argument('name',help='New name')
rename_parser.set_defaults(module=False, topic=False)

batch_parser = subparsers.add_parser('batch', help="Batch process files")
batch_parser.add_argument('action',help='Batch action to perform')

cut_video_parser = subparsers.add_parser('cut_video', help="Cut video file")
cut_video_parser.add_argument('id', help='ID of video file')

rip_audio_parser = subparsers.add_parser('rip_audio', help="Rip audio from video file")
rip_audio_parser.add_argument('id', help='ID of video_file')

update_audio_parser = subparsers.add_parser('update_audio', help="Replace audio in video with its' file in the Audio folder")
update_audio_parser.add_argument('vid', help='ID of video file')
update_audio_parser.add_argument('aid', help='ID of audio file')
update_audio_parser.set_defaults(aid=None)

start_parser = subparsers.add_parser('start', help="Start file in OS")
start_parser.add_argument('id', help='ID of file')

concat_parser = subparsers.add_parser('concat', help="Concatenate video files")
concat_parser.add_argument('--out', help="Output file path", dest="outpath")
concat_parser.set_defaults(outpath=None)
concat_parser.add_argument('ids', nargs='+', help="List of file IDs to concatenate")

file_camrec_parser = subparsers.add_parser('file_camrec', help="File all resources in camrec folder")

add_details_parser = subparsers.add_parser('add_details', help="Add title, event, author details to those videos missing info")

migrate_parser = subparsers.add_parser('migrate', help="Migrate database")

alter_events_parser = subparsers.add_parser('alter_events', help="Alter YRN events")

process_mediasite_event_parser = subparsers.add_parser('process_mediasite_event', help="Process MediaSite event")
process_mediasite_event_parser.add_argument('name', help="Event name")
process_mediasite_event_parser.add_argument('-p', dest="root")
process_mediasite_event_parser.set_defaults(root=MEDIASITE_ROOT)

make_fixture_parser = subparsers.add_parser('make_fixture', help="Make Django fixture")
make_fixture_parser.add_argument('app_name',help="Django app name (lower case)")

remake_video_from_pps_parser = subparsers.add_parser('remake_video_from_pps', help="Remake video using Powerpoint export")
remake_video_from_pps_parser.add_argument('id',help="File ID")
remake_video_from_pps_parser.add_argument('dir',help="Directory containing Powerpoint export")

create_video_from_pps_parser = subparsers.add_parser('create_video_from_pps', help="Create video using Powerpoint show")
create_video_from_pps_parser.add_argument('id',help="File ID")
create_video_from_pps_parser.add_argument('dir',help="Directory to save video")

prune_dead_paths_parser = subparsers.add_parser('prune_dead_paths', help='Prune dead paths')

args = parser.parse_args()

db.connect()

if args.mode == "init":
	create_tables()
elif args.mode == "sync":
	paths = (ROOT,)
	if not args.do_all:
		try:
			paths = [os.path.join(ROOT,path.name) for path in Module.get(Module.working==True).paths]
		except Module.DoesNotExist:
			pass
	print paths
	sync(do_coding=args.do_coding, root_paths=paths)
elif args.mode=="clear_path":
	clear_path_cache(args.path_name)
elif args.mode == "list":
	print args.type
	if args.type=="video":
		files = list_videos(cuts_of=args.cut_of)
	elif args.type=="applications":
		files = list_applications()
	elif args.type=="sound":
		files = list_audio()
	elif args.type=="video_by_event":
		files = list_videos_by_event()
	elif args.type=="no_details":
		files = list(query=_list_no_details_query())
	elif args.type=="events":
		events = _list_events_query()
		for e in events:
			print e.description
	elif args.type=="authors":
		authors = _list_authors_query()
		for a in authors:
			print a.full_name
	else:
		files = list()	
	for line in files:
		try:
			print line
		except UnicodeEncodeError:
			print line.encode('mbcs')
elif args.mode == "workon":
	workon(args.module)
elif args.mode == "dump":
	print json.dumps(dump_codes())
elif args.mode == "load":
	codes = json.loads(sys.stdin.readline())
	load(codes)
elif args.mode == "build":
	create_tables()
	codes = json.loads(sys.stdin.readline())
	load(codes)
	sync(do_coding=args.do_coding)
elif args.mode == "rebuild":
	codes = dump_codes()
	create_tables()
	load(codes)
	sync(do_coding=args.do_coding)
elif args.mode == "struct":
	for line in struct():
		try:
			print line
		except UnicodeEncodeError:
			print line.encode('cp850')
elif args.mode == "rename":
	if args.module:
		try:
			module = Module.get(code=args.module)
		except Topic.DoesNotExist:
			print "Module with code %s not recognised." % (args.module)
		else:
			old_name = module.name
			module.name = args.name
			module.save()
			print "Module renamed from %s to %s" % (old_name, module.name)
	if args.topic:
		try:
			topic = Topic.get(code=args.topic)
		except Topic.DoesNotExist:
			print "Topic with code %s not recognised." % (args.topic)
		else:
			old_name = topic.name
			topic.name = args.name
			topic.save()
			print "Topic renamed from %s to %s" % (old_name, topic.name)
elif args.mode=="batch":
	if args.action =="rip_audio":
		batch_rip_audio()
elif args.mode=="rip_audio":
	rip_audio(File.get(id=args.id))
elif args.mode=="update_audio":
	try:
		update_audio(File.get(id=args.vid),File.get(id=args.aid))
	except File.DoesNotExist:
		update_audio(File.get(id=args.vid))
elif args.mode=="cut_video":
	cut_video(os.path.join(ROOT,File.get(id=args.id).path))
elif args.mode=="start":
	try:
		os.startfile(os.path.join(ROOT,File.get(id=args.id).path))
	except:
		print "Cannot start"
elif args.mode=="concat":
	paths = [os.path.join(ROOT,File.get(id=fid).path) for fid in args.ids]
	sizes = []
	outpath = args.outpath
	if outpath is None:
		outpathroot,basename = os.path.split(paths[0])
		outpath = os.path.join(outpathroot,"_".join([str(fid) for fid in args.ids])+"_moviepy_concat.mp4")
	concat_video(paths,outpath)

elif args.mode=="file_camrec":
	for root, dirs, files in os.walk(CAMREC_ROOT):
		for f in files:
			path = os.path.join(root,f)
			type, size = _get_file_details(path)
			if type=="video":
				file_new_resource(path)

elif args.mode=="deactivate":
	workon(None)

elif args.mode=="add_details":
	files = _list_no_details_query()
	for f in [f for f in files]:
		path = f.path
		full_path = os.path.join(ROOT,path)
		print "Adding details for %s" % path
		yn = yn_input("Show resource?")
		if yn=="Y":
			os.startfile(full_path)
		yn = yn_input("Use resource?")
		if yn=="Y":
			add_resource_details(f)
		else:
			try:
				dest_path = os.path.join(UNUSED_VIDEO_ROOT,f.suggested_filename())
			except (AttributeError, TypeError):
				dest_path = os.path.join(UNUSED_VIDEO_ROOT, os.path.basename(f.path))
			print "Moving %s to %s" % (full_path, dest_path)
			try:
				os.rename(full_path,dest_path)
			except:
				print "Orphaned file: %s" % full_path
			f.delete_instance()

elif args.mode=="migrate":
	do_migrate()

elif args.mode=="list_events_to_alter":
	files = _list_videos_query()
	for f in files:
		try:
			if f.event.description == "YRN Workshop York: Apr 2015":
				print f.id, f.path
		except AttributeError:
			print f.event

elif args.mode=="alter_events":
	files = _list_videos_query()
	for f in files:
		if f.event is None:
			continue
		if f.event.description == "YRN Workshop York: Apr 2015":
			print f.path
			alter_event(f)

elif args.mode=="process_mediasite_event":
	for d in [os.path.join(args.root,d) for d in os.listdir(args.root) if os.path.isdir(os.path.join(args.root,d)) ]:
		print "Processing %s" % d
		yn = yn_input("Skip?")
		if yn=="Y":
			continue
		videopath = os.path.join(TEMP_VIDEO_ROOT,get_video_name_from_mediasite_dir(d))
		yn = yn_input("Skip video generation?")
		if yn=="N":
				video = get_videoclip_from_mediasite_dir(d)
				#video.audio.to_audiofile(os.path.join(TEMP_VIDEO_ROOT,"temp_audio.mp3"))
				video.write_videofile(videopath,fps=2)
		f,authors = get_cmsfile_from_mediasite_dir(args.name,d,videopath)


		if f is not None:
			root,basename = os.path.split(videopath)
			with db.atomic() as txn:
				try:
					f.save()
				except IntegrityError:
					f = File.get(path = f.path)
				for author in authors:
					AuthorsOfFile.create(file=f,author=author)
				f.path = os.path.join(f.containing_path.name,f.suggested_filename())
				try:
					f.save()
				except:
					pass
				source = videopath
				dest = os.path.join(ROOT,f.path)
				print "Moving %s to %s" % (source, dest)
				os.rename(source,dest)
		else:
			"Skipping this file."

elif args.mode=="make_fixture":
	make_django_fixture(args.app_name)

elif args.mode=="remake_video_from_pps":
	res = File.get(id=args.id)
	video = remake_videoclip_from_pps_dir(res,args.dir)
	root,name = os.path.split(res.path)
	basename,ext = os.path.splitext(name)
	video.write_videofile(os.path.join(args.dir,"%s_pps_remade%s" % (basename,ext)),fps=24)

elif args.mode=="create_video_from_pps":
	pps = File.get(id=args.id)
	video = create_videoclip_from_pps(os.path.join(ROOT,pps.path))
	root,name = os.path.split(pps.path)
	basename,ext = os.path.splitext(name)
	video.write_videofile(os.path.join(args.dir,"%s_pps_remade%s" % (basename,".mp4")),fps=24)

elif args.mode=="prune_dead_paths":
	prune_dead_paths()

db.close()