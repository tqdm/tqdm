from pytest import fixture, importorskip, mark, skip


def test_tk_import():
    importorskip('tqdm.tk')


@fixture
def tk():
    module = importorskip('tqdm.tk')
    try:
        root = module.tkinter.Tk()
    except module.tkinter.TclError as exc:
        skip(f"Tk display unavailable: {exc}")
    root.withdraw()
    yield module, root
    root.destroy()


@mark.filterwarnings("ignore:GUI is experimental/alpha:tqdm.std.TqdmExperimentalWarning")
@mark.parametrize("total, initial", [(10, 0), (10, 4), (None, 0), (None, 3),
                                     (0, 0), (float('inf'), 0)])
def test_tk_initial_display(tk, total, initial):
    module, root = tk
    with module.tqdm(total=total, initial=initial, tk_parent=root) as bar:
        assert bar._tk_window.winfo_ismapped()
        assert bar._tk_n_var.get() == initial
        assert bar._tk_text_var.get()
        assert bar.n == initial
        assert bar.last_print_n == initial


@mark.filterwarnings("ignore:GUI is experimental/alpha:tqdm.std.TqdmExperimentalWarning")
def test_tk_delayed_initial_display(tk):
    module, root = tk
    with module.tqdm(total=10, delay=60, tk_parent=root) as bar:
        assert not bar._tk_window.winfo_ismapped()
        assert not bar._tk_text_var.get()
        bar.refresh()
        assert bar._tk_window.winfo_ismapped()
        assert bar._tk_text_var.get()


def test_tk_disabled(tk):
    module, root = tk
    with module.tqdm(total=10, disable=True, tk_parent=root) as bar:
        assert not hasattr(bar, '_tk_window')


@mark.filterwarnings("ignore:GUI is experimental/alpha:tqdm.std.TqdmExperimentalWarning")
def test_tk_initial_display_in_mainloop(tk):
    module, root = tk
    bars = []

    def create_bar():
        bars.append(module.tqdm(total=10, initial=4, tk_parent=root))
        root.after(20, root.quit)

    root.after(0, create_bar)
    root.after(5000, root.quit)
    try:
        root.mainloop()
        assert len(bars) == 1
        bar = bars[0]
        assert bar._tk_dispatching
        assert bar._tk_window.winfo_ismapped()
        assert bar._tk_n_var.get() == 4
        assert bar._tk_text_var.get()
    finally:
        for bar in bars:
            bar.close()
