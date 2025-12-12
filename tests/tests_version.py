"""Test `tqdm.__version__`."""
import re
from ast import literal_eval


def test_version():
    """Test version string"""
    from tqdm import __version__
    if __version__ != "UNKNOWN":
        match = re.match(
            r"^(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+|dev\w*))?",
            __version__,
        )
        assert match, "must start with Major.minor[.patch]"
        major, minor, patch = match.group("major", "minor", "patch")
        assert all(
            isinstance(literal_eval(i), int) for i in (major, minor)
        ), "Version Major.minor must be integers"
        assert (
            patch is None or patch.startswith("dev")
            or isinstance(literal_eval(patch), int)
        ), "Patch must be integer when present unless local dev build"
