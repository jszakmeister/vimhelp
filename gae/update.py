import os, re, sys, logging
from google.appengine.api import urlfetch
from vimh2h import VimH2H
from dbmodel import *
from update_common import *

# Once we have consumed about 30 seconds of CPU time, Google will throw us a
# DeadlineExceededError and our script terminates. Therefore, we must be careful
# with the order of operations, to ensure that after this has happened, the next
# scheduled run of the script can pick up where the previous one was
# interrupted.

force = (os.environ.get('QUERY_STRING') == 'force')

de_upfs = { }
for upf in UnprocessedFile.all():
    if upf.url.startswith('de/'):
        de_upfs[upf.url] = upf

class FileFromServer:
    def __init__(self, content, modified, upf):
	self.content = content
	self.modified = modified
	self.upf = upf

    def write_to_cache(self):
	if self.upf is not None: self.upf.put()

def fetch(url, write_to_cache = True, use_etag = True):
    dbrecord = UnprocessedFile.all().filter('url =', url).get()
    headers = { }
    if dbrecord is not None and dbrecord.etag is not None and use_etag:
	logging.debug("for %s, saved etag is %s", url, dbrecord.etag)
	headers['If-None-Match'] = dbrecord.etag
    result = urlfetch.fetch(url, headers = headers, deadline = 10)
    if result.status_code == 304 and dbrecord is not None:
	logging.debug("url %s is unchanged", url)
	return FileFromServer(dbrecord.data, False, None)
    elif result.status_code != 200:
	log_error("bad HTTP response %d when fetching url %s",
		result.status_code, url)
	sys.exit()
    if dbrecord is None:
	dbrecord = UnprocessedFile(url = url)
    dbrecord.data = result.content
    dbrecord.etag = result.headers.get('ETag')
    if write_to_cache:
	dbrecord.put()
    logging.debug("fetched %s", url)
    return FileFromServer(result.content, True, dbrecord)

index = fetch(BASE_URL).content

print "Content-Type: text/html\n"

log_info("starting update")

skip_help = False

m = re.search('<title>Revision (.+?): /runtime/doc</title>', index)
if m:
    rev = m.group(1)
    dbreposi = VimRepositoryInfo.all().get()
    if dbreposi is not None:
	if dbreposi.revision == rev:
	    if not force:
		log_info("revision %s unchanged, nothing to do (except for faq)", rev)
		dbreposi = None
		skip_help = True
	    else:
		log_info("revision %s unchanged, continuing anyway", rev)
		dbreposi.delete()
		dbreposi = VimRepositoryInfo(revision = rev)
	else:
	    log_info("new revision %s (old %s)", rev, dbreposi.revision)
	    dbreposi.revision = rev
    else:
	log_info("encountered revision %s, none in db", rev)
	dbreposi = VimRepositoryInfo(revision = rev)
else:
    log_warning("revision not found in index page")

tags = fetch(TAGS_URL).content

h2h = VimH2H(tags)

log_debug("processed tags")

pfs = { }
for pf in ProcessedFile.all():
    if not pf.filename.startswith('de/'):  # TODO a bit brittle this...
        if force:
            pf.redo = True
            pf.put()
        pfs[pf.filename] = pf

filenames = set()

count = 0

if not skip_help:
    for match in re.finditer(r'[^-\w]([-\w]+\.txt|tags)[^-\w]', index):
	filename = match.group(1)
	if filename in filenames: continue
	filenames.add(filename)
	count += 1
	f = fetch(BASE_URL + filename, False)
	filenamehtml = filename + '.html'
	pf = pfs.get(filenamehtml)
	if pf is None or pf.redo or f.modified:
	    html = h2h.to_html(filename, f.content)
	    store(filenamehtml, html, pf)
	else:
	    print "<p>File", filename, "is unchanged</p>"
	f.write_to_cache()

if dbreposi is not None: dbreposi.put()

filename = 'vim_faq.txt'
filenamehtml = filename + '.html'
f = fetch(FAQ_URL, False, False)  # for now, don't use ETag -- causes problems here
pf = pfs.get(filenamehtml)
if pf is None or pf.redo or f.modified:
    h2h.add_tags(filename, f.content)
    html = h2h.to_html(filename, f.content)
    store(filenamehtml, html, pf)
    f.write_to_cache()
else:
    print "<p>FAQ is unchanged</p>"

log_info("finished update")

