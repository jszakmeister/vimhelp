import sys, os, re, logging, bz2
from dbmodel import ProcessedFile
from google.appengine.api import memcache

CONTENT_TYPE = 'Content-Type: text/html; charset=utf-8\n'

def notfound(msg = None):
    logging.info("file not found, msg = " + msg)
    print "Status: 404 Not Found"
    print CONTENT_TYPE
    print '<p>Not found</p>'
    if msg: print msg
    sys.exit()

path_info = os.environ['PATH_INFO']
if path_info == '/':
    filename = 'help.txt.html'
elif path_info in ('/de', '/de/'):
    filename = 'de/help.txt.html'
else:
    m = re.match(r"/((?:de/)?(?:.*?\.txt|tags)\.html)$", path_info)
    if not m: notfound("illegal url")
    filename = m.group(1)

cached = memcache.get(filename)
if cached is not None:
    print CONTENT_TYPE
    print bz2.decompress(cached)
else:
    record = ProcessedFile.all().filter('filename =', filename).get()
    if record is None: notfound("not in database")
    memcache.set(filename, record.data)
    print CONTENT_TYPE
    print bz2.decompress(record.data)

