from __future__ import print_function, division

from nose.plugins.skip import SkipTest

from contextlib import contextmanager

import inspect
import re
import sys
from time import time
from bytecode_tracer import BytecodeTracer
from bytecode_tracer import rewrite_function

from tqdm import trange
from tqdm import tqdm

try:
    from StringIO import StringIO
except:
    from io import StringIO
# Ensure we can use `with closing(...) as ... :` syntax
if getattr(StringIO, '__exit__', False) and \
   getattr(StringIO, '__enter__', False):
    def closing(arg):
        return arg
else:
    from contextlib import closing

try:
    _range = xrange
except:
    _range = range


_tic_toc = [None]


def tic():
    _tic_toc[0] = time()


def toc():
    return time() - _tic_toc[0]


btracer = BytecodeTracer()


def trace(frame, event, arg):
    '''Custom tracer callback with bytecode offset instead of line number'''
    bytecode_events = list(btracer.trace(frame, event))
    if bytecode_events:
        for ev, rest in bytecode_events:
            if ev == 'c_call':
                func, pargs, kargs = rest
                print("C_CALL", func.__name__, repr(pargs), repr(kargs))
            elif ev == 'c_return':
                print("C_RETURN", repr(rest))
            elif ev == 'print':
                print("PRINT", repr(rest))
            elif ev == 'print_to':
                value, output = rest
                print("PRINT_TO", repr(value), repr(output))
            else:
                print("C_OTHER:", repr(value), repr(rest))
    else:
        if event == 'call':
            args = inspect.getargvalues(frame)
            try:
                args = str(args)
            except Exception:
                args = "<unknown>"
            print("CALL", frame.f_code.co_name, args)
        elif event == 'return':
            print("RETURN", frame.f_code.co_name, repr(arg))
        elif event == 'exception':
            print("EXCEPTION", arg)
        elif event == 'line':
            # Most important statement for us: show each executed line and its
            # bytecode offset
            print("LINE", frame.f_code.co_filename, frame.f_lineno)
        else:
            print("OTHER", event, frame.f_code.co_name, repr(arg))
    return trace


@contextmanager
def captureStdOut(output):
    '''Capture stdout temporarily, use along a with statement'''
    stdout = sys.stdout
    sys.stdout = output
    yield
    sys.stdout = stdout


def getOpcodes(func, *args, **kwargs):
    '''Get the bytecode opcodes for a function'''
    # Redirect all printed outputs to a variable
    out = StringIO()
    with captureStdOut(out):
        # Setup bytecode tracer
        btracer.setup()

        #  dis.dis(func)  # not needed in our case

        # Rewrite the function to allow bytecode tracing
        rewrite_function(func)

        # Start the tracing
        sys.settrace(trace)
        try:
            # Execute the function
            func(*args, **kwargs)
        finally:
            # Stop the tracer
            sys.settrace(None)
            btracer.teardown()

    return out


def getOpcodesCount(func, *args, **kwargs):
    '''Get the total number of bytecode opcodes for a function'''
    out = getOpcodes(func, *args, **kwargs)

    # Filter tracing events to keep only executed lines
    opcodes = [s for s in out.getvalue().split('\n')
               if s.startswith('LINE') or s.startswith('C_CALL')]

    # Return the total number of opcodes
    return len(opcodes)


def getOpcodesCountHard(func, *args, **kwargs):
    '''Get the total number of bytecode opcodes for a function (pessimistic)'''
    out = getOpcodes(func, *args, **kwargs)

    # Hard mode: extract bytecode offsets and get the highest number for each
    # sequence, this should theoretically compute the exact timesteps taken for
    # each statement.
    # TODO: not sure this is correct, we may be overestimating a lot!
    RE_opcodes = re.compile(r'\S+\s+\S+\s+(\d+)')
    opcodes = [s for s in out.getvalue().split('\n') if s.startswith('LINE')]
    opcodes_offsets = [int(RE_opcodes.search(s).group(1))
                       if s.startswith('LINE') else 0 for s in opcodes]

    opcodes_total = 0
    for i in _range(1, len(opcodes_offsets)):
        if opcodes_offsets[i] <= opcodes_offsets[i - 1]:
            opcodes_total += opcodes_offsets[i]
    opcodes_total += opcodes_offsets[-1]

    return opcodes_total


def test_iter_overhead():
    """ Test overhead of iteration based tqdm """
    total = int(1e6)

    with closing(StringIO()) as our_file:
        a = 0
        tic()
        for i in trange(total, file=our_file):
            a += i
        time_tqdm = toc()
        assert(a == (total * total - total) / 2.0)

    a = 0
    tic()
    for i in _range(total):
        a += i
    time_bench = toc()

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm < 9 * time_bench)
    except AssertionError:
        raise AssertionError('trange(%g): %f, range(%g): %f' %
                             (total, time_tqdm, total, time_bench))


def test_manual_overhead():
    """ Test overhead of manual tqdm """
    total = int(1e6)

    with closing(StringIO()) as our_file:
        t = tqdm(total=total * 10, file=our_file, leave=True)
        a = 0
        tic()
        for i in _range(total):
            a += i
            t.update(10)
        time_tqdm = toc()

    a = 0
    tic()
    for i in _range(total):
        a += i
    time_bench = toc()

    # Compute relative overhead of tqdm against native range()
    try:
        assert(time_tqdm < 19 * time_bench)
    except AssertionError:
        raise AssertionError('tqdm(%g): %f, range(%g): %f' %
                             (total, time_tqdm, total, time_bench))


def test_iter_overhead_hard_opcodes():
    """ Test overhead of iteration based tqdm (hard with opcodes) """
    try:
        import imputil
    except ImportError:
        raise SkipTest

    total = int(10)

    def f1():
        with closing(StringIO()) as our_file:
            a = 0
            for i in trange(total, file=our_file, leave=True,
                            miniters=1, mininterval=0, maxinterval=0):
                a += i
            assert(a == (total * total - total) / 2.0)

    def f2():
        with closing(StringIO()) as our_file:
            a = 0
            for i in _range(total):
                a += i
                our_file.write(("%i" % a) * 40)

    # Compute opcodes overhead of tqdm against native range()
    count1 = getOpcodesCount(f1)
    count2 = getOpcodesCount(f2)
    count1h = getOpcodesCountHard(f1)
    count2h = getOpcodesCountHard(f2)
    try:
        assert(count1 < 7 * count2)
        # assert(count1h < 20 * count2h)  # useless to test static bytecode
    except AssertionError:
        raise AssertionError('trange(%g): %i-%i, range(%g): %i-%i' %
                             (total, count1, count1h, total, count2, count2h))


def test_manual_overhead_hard_opcodes():
    """ Test overhead of manual tqdm (hard with opcodes) """
    try:
        import imputil
    except ImportError:
        raise SkipTest

    total = int(10)

    def f1():
        with closing(StringIO()) as our_file:
            t = tqdm(total=total * 10, file=our_file, leave=True,
                     miniters=1, mininterval=0, maxinterval=0)
            a = 0
            for i in _range(total):
                a += i
                t.update(10)

    def f2():
        with closing(StringIO()) as our_file:
            a = 0
            for i in _range(total):
                a += i
                our_file.write(("%i" % a) * 40)

    # Compute opcodes overhead of tqdm against native range()
    count1 = getOpcodesCount(f1)
    count2 = getOpcodesCount(f2)
    count1h = getOpcodesCountHard(f1)
    count2h = getOpcodesCountHard(f2)
    try:
        assert(count1 < 20 * count2)
        # assert(count1h < 20 * count2h)  # useless to test static bytecode
    except AssertionError:
        raise AssertionError('tqdm(%g): %i-%i, range(%g): %i-%i' %
                             (total, count1, count1h, total, count2, count2h))
