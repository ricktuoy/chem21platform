import os
if 'DJANGO_DEVELOPMENT' in os.environ:
	from local import *
else:
	from production import *
