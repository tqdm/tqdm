from .utils import CUR_OS, IS_WIN, IS_NIX, RE_ANSI, _range, _unich, _unicode, colorama, WeakSet, _basestring, _OrderedDict, FormatReplace, Comparable, SimpleTextIOWrapper, _is_utf, _supports_unicode, _is_ascii, _environ_cols_wrapper, _environ_cols_windows, _environ_cols_tput, _environ_cols_linux, _term_move_up  # NOQA
from .std import TqdmDeprecationWarning
from warnings import warn
warn("This function will be removed in tqdm==5.0.0\n"
     "Please use `tqdm.utils.*` instead of `tqdm._utils.*`",
     TqdmDeprecationWarning)
