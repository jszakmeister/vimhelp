import sys, logging, cgi, bz2, zipfile, StringIO
from google.appengine.api import urlfetch, memcache
from vimh2h import VimH2H, LANG_DE, LANG_DE_NA
from dbmodel import *
from update_common import *

HEADER = """
<html><head><title>German Vimhelp Updater</title></head><body>
<h1>German Vimhelp Updater</h1>
"""

FOOTER = '</body></html>'

def zipfilename_to_de_url(zfn):
    if zfn.endswith(".dex"):
        return "de/" + zfn[:-4] + ".txt"
    elif zfn == "tags-de":
        return "de/tags"
    else:
        log_warning("unexpected zipped file name %s", zfn)
        return "de/" + zfn

def fetch(url):
    print HEADER
    upfs = { }
    for upf in UnprocessedFile.all():
        upfs[upf.url] = upf
    print "<p>Fetching " + url + ".</p> "
    result = urlfetch.fetch(url)
    if result.status_code != 200:
	log_error("bad HTTP response %d when fetching url %s",
		result.status_code, url)
	sys.exit()
    zipdata = StringIO.StringIO(result.content)
    zipf = zipfile.ZipFile(zipdata, 'r')
    print "<b>Zip file contents:</b><br>"
    for zn in zipf.namelist():
        zdata = zipf.read(zn)
        de_url = zipfilename_to_de_url(zn)
        print zn + " -&gt; " + de_url + "<br>"
        upf = upfs.get(de_url)
        if upf is None: upf = UnprocessedFile(url = de_url)
        upf.data = zdata
        upf.put()
    zipf.close()
    print '<p><a href="update_de?process=1">Now process them!</a></p>'
    print FOOTER

def process():
    print HEADER
    upfs = { }
    for upf in UnprocessedFile.all():
        upfs[upf.url] = upf
    print 'I have ' + str(len(upfs)) + ' unprocessed files<br>'
    tags = upfs[TAGS_URL].data
    de_tags = upfs['de/tags'].data
    pfs = { }
    for pf in ProcessedFile.all():
        if pf.filename.startswith('de/'):
            pfs[pf.filename] = pf
    h2h = VimH2H(tags, LANG_DE)
    h2h.add_tags(de_tags, LANG_DE)
    for upf in upfs.itervalues():
        url = upf.url
        if url.startswith(BASE_URL) and len(url) > len(BASE_URL):
            filename = str(url[len(BASE_URL):])
            de_url = 'de/' + filename
            de_upf = upfs.get(de_url)
            if de_upf is not None:
                log_info("Processing " + filename + " (German)")
                html = h2h.to_html(filename, de_upf.data,
                        language = LANG_DE)
            else:
                log_info("Processing " + filename + " (English)")
                html = h2h.to_html(filename, upf.data,
                        language = LANG_DE_NA)
            filenamehtml = de_url + '.html'
            pf = pfs.get(filenamehtml)
            store(filenamehtml, html, pf)
    print FOOTER

def show_url_form():
    print HEADER
    print '<form method="get">'
    print 'URL: '
    print '<input type="text" name="url" size="80">'
    print '<input type="submit" value="OK">'
    print '</form>'
    print FOOTER

print "Content-type: text/html\n"

form = cgi.FieldStorage()

if "url" in form:
    fetch(form.getfirst("url"))
elif "process" in form:
    process()
else:
    show_url_form()

