from tqdm.utils import envwrap


def test_envwrap(monkeypatch):
    """Test envwrap overrides"""
    env_a = 42
    env_c = 1337
    monkeypatch.setenv('FUNC_A', str(env_a))
    monkeypatch.setenv('FUNC_TyPe_HiNt', str(env_c))

    @envwrap("FUNC_")
    def func(a=1, b=2, type_hint: int = None):
        return a, b, type_hint

    assert (env_a, 2, 1337) == func(), "expected env override"
    assert (99, 2, 1337) == func(a=99), "expected manual override"

    env_liTeral = 3.14159
    monkeypatch.setenv('FUNC_liTeral', str(env_liTeral))

    @envwrap("FUNC_", literal_eval=True, case_sensitive=True)
    def another_func(liTeral=1):
        return liTeral

    assert env_liTeral == another_func()
