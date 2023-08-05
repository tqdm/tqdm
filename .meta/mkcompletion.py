"""
Auto-generate tqdm/completion.sh from docstrings.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import tqdm  # NOQA
import tqdm.cli  # NOQA

RE_OPT = re.compile(r'(\w+)  :', flags=re.M)
RE_OPT_INPUT = re.compile(r'(\w+)  : (?:str|int|float|chr|dict|tuple)', flags=re.M)


def doc2opt(doc, user_input=True):
    """
    doc  : str, document to parse
    user_input  : bool, optional.
      [default: True] for only options requiring user input
    """
    RE = RE_OPT_INPUT if user_input else RE_OPT
    return ('--' + i for i in RE.findall(doc))


# CLI options
options = {'-h', '--help', '-v', '--version'}
options_input = set()
for doc in (tqdm.tqdm.__doc__, tqdm.cli.CLI_EXTRA_DOC):
    options.update(doc2opt(doc, user_input=False))
    options_input.update(doc2opt(doc, user_input=True))
options.difference_update('--' + i for i in ('name',) + tqdm.cli.UNSUPPORTED_OPTS)
options_input &= options
options_input -= {"--log"}  # manually dealt with
completion = u"""\
#!/usr/bin/env bash
_tqdm(){{
  local cur prv
  cur="${{COMP_WORDS[COMP_CWORD]}}"
  prv="${{COMP_WORDS[COMP_CWORD - 1]}}"

  case ${{prv}} in
  {opts_manual})
    # await user input
    ;;
  "--log")
    COMPREPLY=($(compgen -W \
      'CRITICAL FATAL ERROR WARN WARNING INFO DEBUG NOTSET' -- ${{cur}}))
    ;;
  *)
    COMPREPLY=($(compgen -W '{opts}' -- ${{cur}}))
    ;;
  esac
}}
complete -F _tqdm tqdm
""".format(opts=' '.join(sorted(options)), opts_manual='|'.join(sorted(options_input)))

if __name__ == "__main__":
    (Path(__file__).resolve().parent.parent / 'tqdm' / 'completion.sh').write_text(
        completion, encoding='utf-8')
