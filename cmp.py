#!/usr/bin/python3

# Verifies that those tags which appear in both doc/tags and de/tags-de refer to
# the same position in the same source files.  Since this is true, it is safe to
# generate those German files for which no translation is available without
# using de/tags-de.

import sys

def read_tags(fn):
    tags = { }
    with open(fn) as f:
        for line in f:
            tag, srcfn, pos = line.split('\t')
            tags[tag] = (srcfn, pos)
    return tags

tags_en = read_tags('doc/tags')
tags_de = read_tags('de/tags-de')

all_is_well = True

for tag in tags_de:
    if tag not in tags_en: continue
    srcfn_de, pos_de = tags_de[tag]
    if srcfn_de.endswith('.dex'): srcfn_de = srcfn_de[:-4] + '.txt'
    srcfn_en, pos_en = tags_en[tag]
    if (srcfn_de, pos_de) != (srcfn_en, pos_en):
        all_is_well = False
        print(tag, tags_de[tag], tags_en[tag])

if all_is_well:
    print('All is well.')
    sys.exit(0)
else:
    print('All is not well!')
    sys.exit(1)

