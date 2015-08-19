import os
if 'DJANGO_DEVELOPMENT' in os.environ:
	from local import *
elif 'DJANGO_TESTING' in os.environ:
	from testing import *
else:
	from production import *