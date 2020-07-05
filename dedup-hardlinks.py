#!/usr/bin/env python3

import os
import sys
import hashlib
import argparse
import stat

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

dryrun = True
verbose = False

def relink(f1, f2, nbyte):
    '''Replace `f2` with a hardlink to `f1`.'''
    global dryrun

    stat1 = os.stat(f1)
    stat2 = os.stat(f2)

    if stat1.st_dev != stat2.st_dev:
        die(f'File {f1} and {f2} are on different devices? Perhaps rethink your arguments to find(1)...')

    if stat1.st_ino == stat2.st_ino:
        if verbose:
            print(f'Skipping, because {f1} and {f2} are already hardlinked')
        return

    if not stat.S_ISREG(stat1.st_mode) or not stat.S_ISREG(stat2.st_mode):
        if verbose:
            print(f'Skipping, because either {f1} or {f2} are not normal files')
        return

    if dryrun or verbose:
        print("replace %s with hardlink to %s, saving %s" % (f2, f1, prettysize(nbyte)))

    if not dryrun:
        os.unlink(f2)
        os.link(f1, f2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true', default=False, help="describe what is being done")
    parser.add_argument('--dryrun', '-n', action='store_true', default=False, help='check what to do and print it but do not do anything')
    args = parser.parse_args()

    if sys.stdin.isatty():
        die("Usage: find ... -print0 | dedup-hardlinks.py")

    global dryrun
    global verbose
    dryrun = args.dryrun
    verbose = args.verbose

    filelist = read_filelist(sys.stdin)
    nfile = len(filelist)
    print("Read %d filenames" % nfile)
    filedict = {}
    nrelink = 0
    nbyterelink = 0
    nbytestored = 0
    for fn in filelist:
        (h, nbyte) = filehash(fn)
        if nbyte == 0:
            continue
        if h in filedict:
            relink(filedict[h], fn, nbyte)
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
