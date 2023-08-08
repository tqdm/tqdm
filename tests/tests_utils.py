from pytest import mark

from tqdm.utils import IS_WIN, envwrap


def test_envwrap(monkeypatch):
    """Test envwrap overrides"""
    env_a = 42
    env_c = 1337
    monkeypatch.setenv('FUNC_A', str(env_a))
    monkeypatch.setenv('FUNC_TyPe_HiNt', str(env_c))
    monkeypatch.setenv('FUNC_Unused', "x")

    @envwrap("FUNC_")
    def func(a=1, b=2, type_hint: int = None):
        return a, b, type_hint

    assert (env_a, 2, 1337) == func(), "expected env override"
    assert (99, 2, 1337) == func(a=99), "expected manual override"

    env_literal = 3.14159
    monkeypatch.setenv('FUNC_literal', str(env_literal))

    @envwrap("FUNC_", literal_eval=True)
    def another_func(literal="some_string"):
        return literal

    assert env_literal == another_func()


@mark.skipif(IS_WIN, reason="no lowercase environ on Windows")
def test_envwrap_case(monkeypatch):
    """Test envwrap case-sensitive overrides"""
    env_liTeRaL = 3.14159
    monkeypatch.setenv('FUNC_liTeRaL', str(env_liTeRaL))

    @envwrap("FUNC_", literal_eval=True, case_sensitive=True)
    def func(liTeRaL="some_string"):
        return liTeRaL

    assert env_liTeRaL == func()
