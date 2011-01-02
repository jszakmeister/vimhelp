#!/usr/bin/python

import sys
import os.path
#import cProfile

sys.path.append('../gae')

from vimh2h import VimH2H

def slurp(filename):
    f = open(filename)
    c = f.read()
    f.close()
    return c

def usage():
    return "usage: " + sys.argv[0] + " <file>..."

def main():
    if len(sys.argv) < 2: sys.exit(usage())

    print "Processing tags..."
    h2h = VimH2H(slurp('tags'))

    for filename in sys.argv[1:]:
	print "Processing " + filename + "..."
	of = open(filename + '.html', 'w')
	of.write(h2h.to_html(filename, slurp(filename), False, False))
	of.close()

main()

#cProfile.run('main()')
