#!/usr/bin/env python

import sys
import hashlib
import argparse

def die(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit(1)

def read_filelist(fh):
    buf = fh.read()
    if '\0' not in buf:
        die("No NUL found in input (did you forget -print0?)")

    flist = buf.split('\0')
    # drop the empty last item if the list is terminated with a NUL
    if len(flist) > 0 and len(flist[-1]) == 0:
        flist = flist[:-1]
    return flist

def filehash(fname):
    BLKSZ = 1024 * 1024
    h = hashlib.sha1()
    nbyte = 0
    with open(fname, 'rb') as fh:
        while True:
            b = fh.read(BLKSZ)
            if not b:
                break
            nbyte += len(b)
            h.update(b)
    return (h.digest(), nbyte)

def prettysize(nbyte):
    if nbyte < 1024:
        return "%d B" % nbyte
    prefixes = ['%siB' % s for s in 'kMGTPEY']
    for p in prefixes:
        nbyte /= 1024
        if nbyte < 1024:
            return "%d %s" % (nbyte, p)

def relink(f1, f2):
    '''Replace `f2` with a hardlink to `f1`.'''
    print("replace %s with hardlink to %s" % (f2, f1))

def main():
    parser = argparse.ArgumentParser()
    #parser.add_argument()
    args = parser.parse_args()

    if sys.stdin.isatty():
        die("Usage: find ... -print0 | dedup-hardlinks.py")

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
