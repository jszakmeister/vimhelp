import os, logging, bz2
from google.appengine.api import memcache
from dbmodel import ProcessedFile

BASE_URL = 'http://vim.googlecode.com/hg/runtime/doc/'
TAGS_URL = BASE_URL + 'tags'
FAQ_URL = 'http://github.com/chrisbra/vim_faq/raw/master/doc/vim_faq.txt'

is_dev = (os.environ.get('SERVER_NAME') == 'localhost')

if is_dev:
    logging.getLogger().setLevel(logging.DEBUG)

def do_log(msg, args, logfunc, html_msg = None):
    msg = msg % args
    logfunc(msg)
    if html_msg is None: html_msg = "<p>" + msg + "</p>"
    print html_msg

def log_debug(msg, *args): do_log(msg, args, logging.debug)
def log_info(msg, *args): do_log(msg, args, logging.info)
def log_warning(msg, *args):
    do_log(msg, args, logging.info, "<p><b>" + msg + "</b></p>")
def log_error(msg, *args):
    do_log(msg, args, logging.error, "<h2>" + msg + "</h2>")

def store(filename, content, pf):
    if pf is None:
	pf = ProcessedFile(filename = filename)
    compressed = bz2.compress(content)
    pf.data = compressed
    pf.redo = False
    memcache.set(filename, compressed)
    pf.put()
    log_debug("Processed file %s", filename)

