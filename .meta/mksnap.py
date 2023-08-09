# -*- encoding: utf-8 -*-
"""
Auto-generate snapcraft.yaml.
"""
import sys
from pathlib import Path
from subprocess import check_output  # nosec

sys.path.insert(1, str(Path(__file__).parent.parent))
import tqdm  # NOQA

snap_yml = r"""name: tqdm
summary: A fast, extensible CLI progress bar
description: |
 https://tqdm.github.io

 `tqdm` means "progress" in Arabic (taqadum, تقدّم) and is an
 abbreviation for "I love you so much" in Spanish (te quiero demasiado).

 Instantly make your loops show a smart progress meter and stats - just
 replace any pipe "`|`" with "`| tqdm |`", and you're done!

 ```sh
 $ seq 9999999 | tqdm --bytes | wc -l
 75.2MB [00:00, 217MB/s]
 9999999
 $ 7z a -bd -r backup.7z docs/ | grep Compressing | \
     tqdm --total $(find docs/ -type f | wc -l) --unit files >> backup.log
 100%|███████████████████████████████▉| 8014/8014 [01:37<00:00, 82.29files/s]
 ```

 Overhead is low -- about 60ns per iteration.

 In addition to its low overhead, `tqdm` uses smart algorithms to predict
 the remaining time and to skip unnecessary iteration displays, which
 allows for a negligible overhead in most cases.

 `tqdm` works on any platform (Linux, Windows, Mac, FreeBSD, NetBSD,
 Solaris/SunOS), in any console or in a GUI, and is also friendly with
 IPython/Jupyter notebooks.

 `tqdm` does not require any dependencies, just
 an environment supporting `carriage return \r` and
 `line feed \n` control characters.
grade: stable
confinement: strict
base: core22
icon: logo.png
version: '{version}'
license: MPL-2.0
parts:
  tqdm:
    plugin: python
    source: .
    source-commit: '{commit}'
    python-packages: [.]
    build-packages: [git]
    override-build: |
        craftctl default
        cp $SNAPCRAFT_PART_BUILD/tqdm/completion.sh $SNAPCRAFT_PART_INSTALL/
apps:
  tqdm:
    command: bin/tqdm
    completer: completion.sh
""".format(version=tqdm.__version__, commit=check_output([
    'git', 'describe', '--always']).decode('utf-8').strip())  # nosec

if __name__ == "__main__":
    (Path(__file__).resolve().parent.parent / 'snapcraft.yaml').write_text(
        snap_yml.decode('utf-8') if hasattr(snap_yml, 'decode') else snap_yml, encoding='utf-8')
