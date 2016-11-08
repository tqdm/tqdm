# -*- coding: utf-8 -*-
"""Usage:
  7zx.py [--help | options] <zipfiles>...

Options:
  -h, --help     Print this help and exit
  -v, --version  Print version and exit
  -c, --compressed       Use compressed (instead of uncompressed) file sizes
  -y, --yes      Assume yes to all queries (for extraction)
  -D=<level>, --debug=<level>
                 Print various types of debugging information. Choices:
                         CRITICAL|FATAL
                         ERROR
                         WARN(ING)
                         [default: INFO]
                         DEBUG
                         NOTSET
  -d, --debug-trace      Print lots of debugging information (-D NOTSET)
"""
from __future__ import print_function
from docopt import docopt
import logging as log
import subprocess
import re
from tqdm import tqdm
from distutils.spawn import find_executable
__author__ = "Casper da Costa-Luis <casper.dcl@physics.org>"
__licence__ = "MPLv2.0"
__version__ = "0.1.0"
__license__ = __licence__


RE_SCN = re.compile("([0-9]+)\s+([0-9]+)\s+(.*)$", flags=re.M)


def main():
    args = docopt(__doc__, version=__version__)
    if args.pop('--debug-trace', False):
        args['--debug'] = "NOTSET"
    log.basicConfig(level=getattr(log, args['--debug'], log.INFO),
                    format='%(levelname)s: %(message)s')
    log.debug(args)

    # Get compressed sizes
    zips = {}
    for fn in args['<zipfiles>']:
        info = subprocess.check_output(["7z", "l", fn]).strip()
        finfo = RE_SCN.findall(info)

        # builtin test: last line should be total sizes
        log.debug(finfo)
        totals = map(int, finfo[-1][:2])
        # log.debug(totals)
        for s in range(2):
            assert(sum(map(int, (inf[s] for inf in finfo[:-1]))) == totals[s])
        fcomp = dict((n, int(c if args['--compressed'] else u))
                     for (u, c, n) in finfo[:-1])
        # log.debug(fcomp)
        zips[fn] = fcomp

    # Extract
    cmd7zx = ["7z", "x", "-bd"]
    if args['--yes']:
        cmd7zx += ["-y"]
    if find_executable("stdbuf"):
        # Force 7z to flush per-line (finer progress)
        cmd7zx = ["stdbuf", "-oL"] + cmd7zx
    log.info("Extracting from {:d} file(s)".format(len(zips)))
    with tqdm(total=sum(s for fcomp in zips.values()
                        for (_, s) in fcomp.items()),
              unit="B", unit_scale=True) as t:
        for fn, fcomp in zips.items():
            ex = subprocess.Popen(cmd7zx + [fn],
                                  bufsize=1,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            while True:
                l_raw = ex.stdout.readline()
                if not l_raw:
                    break
                l = l_raw.strip()
                if l.startswith("Extracting"):
                    exname = l.lstrip("Extracting").lstrip()
                    t.update(fcomp.get(exname, 0))
                # elif l:
                #     if not any(l.startswith(i) for i in
                #                ("7-Zip ",
                #                 "p7zip Version ",
                #                 "Processing archive: ",
                #                 "Everything is Ok",
                #                 "Folders: ",
                #                 "Files: ",
                #                 "Size: ",
                #                 "Compressed: ")):
                #         t.write(l)
            ex.wait()
main.__doc__ = __doc__


if __name__ == "__main__":
    main()
