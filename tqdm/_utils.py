from .utils import CUR_OS, IS_WIN, IS_NIX, RE_ANSI, _range, _unich, _unicode, colorama, WeakSet, _basestring, _OrderedDict, FormatReplace, Comparable, SimpleTextIOWrapper, _is_utf, _supports_unicode, _is_ascii, _screen_shape_wrapper, _screen_shape_windows, _screen_shape_tput, _screen_shape_linux, _environ_cols_wrapper, _term_move_up  # NOQA
from .std import TqdmDeprecationWarning
from warnings import warn
warn("This function will be removed in tqdm==5.0.0\n"
     "Please use `tqdm.utils.*` instead of `tqdm._utils.*`",
     TqdmDeprecationWarning, stacklevel=2)
