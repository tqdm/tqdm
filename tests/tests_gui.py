from pytest import approx, fixture, importorskip, mark, skip


def test_gui_import():
    importorskip('tqdm.gui')


@fixture
def gui():
    tk = importorskip('tkinter')
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        skip(f"Tk display unavailable: {exc}")
    root.destroy()
    plt = importorskip('matplotlib.pyplot')
    backend = plt.get_backend()
    interactive = plt.isinteractive()
    plt.switch_backend('TkAgg')
    plt.ioff()
    yield importorskip('tqdm.gui')
    plt.close('all')
    plt.interactive(interactive)
    plt.switch_backend(backend)


@mark.filterwarnings("ignore:GUI is experimental/alpha:tqdm.std.TqdmExperimentalWarning")
@mark.parametrize("total, initial", [(10, 0), (10, 4), (None, 0), (None, 3),
                                     (0, 0), (float('inf'), 0)])
def test_gui_initial_display(gui, total, initial):
    with gui.tqdm(total=total, initial=initial, leave=False) as bar:
        # The first slow operation can start as soon as construction returns.
        assert bar.fig.canvas.manager.window.winfo_ismapped()
        assert bar.ax.get_title()
        assert bar.fig.canvas.buffer_rgba().shape[0] > 0
        assert not bar.xdata
        assert not bar.ydata
        assert not bar.zdata
        if total and total != float('inf'):
            width = bar.hspan.get_window_extent().width / bar.ax.bbox.width
            assert width == approx(initial / total)
        assert bar.n == initial
        assert bar.last_print_n == initial


@mark.filterwarnings("ignore:GUI is experimental/alpha:tqdm.std.TqdmExperimentalWarning")
def test_gui_delayed_initial_display(gui):
    with gui.tqdm(total=10, delay=60, leave=False) as bar:
        assert not bar.fig.canvas.manager.window.winfo_ismapped()
        assert not bar.ax.get_title()
        bar.refresh()
        assert bar.fig.canvas.manager.window.winfo_ismapped()
        assert bar.ax.get_title()


def test_gui_disabled(gui):
    with gui.tqdm(total=10, disable=True) as bar:
        assert not hasattr(bar, 'fig')


@fixture
def gui_agg():
    plt = importorskip('matplotlib.pyplot')
    backend = plt.get_backend()
    interactive = plt.isinteractive()
    plt.switch_backend('Agg')
    plt.ioff()
    yield importorskip('tqdm.gui')
    plt.close('all')
    plt.interactive(interactive)
    plt.switch_backend(backend)


@mark.filterwarnings("ignore:GUI is experimental/alpha:tqdm.std.TqdmExperimentalWarning")
def test_gui_initial_display_without_elapsed_time(gui_agg, monkeypatch):
    monkeypatch.setattr('tqdm.std.time', lambda: 0)
    with gui_agg.tqdm(total=10, initial=4, leave=False, bar_format="{n}/{total}") as bar:
        assert bar.ax.get_title() == "4/10"
        assert bar.fig.canvas.buffer_rgba().shape[0] > 0
        assert not bar.xdata
        assert not bar.ydata
        assert not bar.zdata
        assert bar.start_t == bar.last_print_t == 0


@mark.filterwarnings("ignore:GUI is experimental/alpha:tqdm.std.TqdmExperimentalWarning")
def test_gui_initial_display_preserves_other_figures(gui_agg, monkeypatch):
    plt = importorskip('matplotlib.pyplot')
    other = plt.figure()
    calls = []
    monkeypatch.setattr(other.canvas, 'flush_events', lambda: calls.append(other))
    with gui_agg.tqdm(total=10, leave=False) as bar:
        assert bar.fig is not other
        assert plt.fignum_exists(other.number)
        assert calls == []
