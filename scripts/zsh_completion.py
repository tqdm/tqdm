#!/usr/bin/env python
import os
import sys
from os.path import dirname as dirn
from typing import Final

path = dirn(dirn((os.path.abspath(__file__))))
sys.path.insert(0, path)
import tqdm  # noqa: E402
from tqdm.cli import CLI_EXTRA_DOC, RE_OPTS  # noqa: E402

d = tqdm.__init__.__doc__ + CLI_EXTRA_DOC  # type: ignore
opt_types = dict(RE_OPTS.findall(d))
split = RE_OPTS.split(d)
opt_types_desc = zip(split[1::3], split[2::3], split[3::3])

PACKAGE: Final = "tqdm"if sys.argv[1:2] == [] else sys.argv[1]
BINNAME: Final = PACKAGE.replace("_", "-")
BINNAMES: Final = [BINNAME]
ZSH_COMPLETION_FILE: Final = (
    "_" + BINNAME if sys.argv[2:3] == [] else sys.argv[2]
)
ZSH_COMPLETION_TEMPLATE: Final = os.path.join(
    dirn(os.path.abspath(__file__)), "zsh_completion.in"
)

flags = []
for o, t, d in opt_types_desc:
    optionstr = "--" + o
    helpstr = (
        " ".join(list(map(str.strip, d.splitlines()[1:])))
        .replace("]", "\\]")
        .replace("'", "'\\''")
    )
    helpstr = "[" + helpstr + "]"

    if t == "bool":
        metavar = ""
    else:
        metavar = t
    if metavar != "":
        # use lowcase conventionally
        metavar = metavar.lower().replace(":", "\\:")

    if metavar == "":
        completion = ""
    elif o == "log":
        completion = "(CRITICAL FATAL ERROR WARN WARNING INFO DEBUG NOTSET)"
    elif o in ["manpath", "comppath"]:
        completion = "_dirs"
    else:
        completion = ""

    if metavar != "":
        metavar = ":" + metavar
    if completion != "":
        completion = ":" + completion

    flag = "{0}'{1}{2}{3}'".format(optionstr, helpstr, metavar, completion)
    flags += [flag]

with open(ZSH_COMPLETION_TEMPLATE) as f:
    template = f.read()

template = template.replace("{{programs}}", " ".join(BINNAMES))
template = template.replace("{{flags}}", " \\\n  ".join(flags))

with (
    open(ZSH_COMPLETION_FILE, "w")
    if ZSH_COMPLETION_FILE != "-"
    else sys.stdout
) as f:
    f.write(template)