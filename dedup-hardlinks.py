#!/usr/bin/env python

import sys
import hashlib
import argparse

def read_filelist(fh):
    buf = fh.read()
    flist = buf.split('\0')
    # drop the empty last item if the list is terminated with a NUL
    if len(flist) > 0 and len(flist[-1]) == 0:
        flist = flist[:-1]
    return flist

def filehash(fname):
    BLKSZ = 1024 * 1024
    h = hashlib.sha1()
    with open(fname, 'rb') as fh:
        while True:
            b = fh.read(BLKSZ)
            if not b:
                break
            h.update(b)
    return h.digest()

def prettysize(nbyte):
    if nbyte < 1024:
        return "%d B" % nbyte
    prefixes = ['%siB' % s for s in 'kMGTPEY']
    for p in prefixes:
        nbyte /= 1024
        if nbyte < 1024:
            return "%d %s" % (nbyte, p)

def main():
    parser = argparse.ArgumentParser()
    #parser.add_argument()
    args = parser.parse_args()

    if sys.stdin.isatty():
        sys.stderr.write("Usage: find ... -print0 | dedup-hardlinks.py\n")
        sys.exit(1)

    filelist = read_filelist(sys.stdin)
    nfile = len(filelist)
    print("Read %d filenames" % nfile)
    filedict = {}
    nrelink = 0
    nbyterelink = 0
    nbytestored = 0
    for fn in filelist:
        (h, nbyte) = filehash(fn)
        if h in filedict:
            relink(filedict[h], fn)
            nrelink += 1
            nbyterelink += nbyte
        else:
            filedict[h] = fn
            nbytestored += nbyte
    print("%d unique / %d total (%d%% duplicates, %s saved / %s used)" % (
            len(filedict),
            nfile,
            100 * (nrelink * 1.0 / nfile),
            prettysize(nbyterelink),
            prettysize(nbytestored)))

if __name__ == '__main__':
    main()
