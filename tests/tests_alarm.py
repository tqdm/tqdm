import sys
import unittest
from io import StringIO
from unittest import mock

from tqdm.std import tqdm


class TestAlarm(unittest.TestCase):

    def _bar(self, **kwargs):
        buf = StringIO()
        return tqdm(total=3, file=buf, **kwargs), buf

    def test_alarm_defaults_to_off(self):
        t, _ = self._bar()
        self.assertFalse(t.alarm)
        t.close()

    def test_alarm_rings_on_completion(self):
        with mock.patch.object(tqdm, '_play_alarm') as play:
            t, _ = self._bar(alarm=True, leave=True)
            t.update(3)
            t.close()
        play.assert_called_once_with()

    def test_no_alarm_when_not_requested(self):
        with mock.patch.object(tqdm, '_play_alarm') as play:
            t, _ = self._bar(leave=True)
            t.update(3)
            t.close()
        play.assert_not_called()

    def test_no_alarm_when_leave_is_false(self):
        with mock.patch.object(tqdm, '_play_alarm') as play:
            t, _ = self._bar(alarm=True, leave=False)
            t.update(3)
            t.close()
        play.assert_not_called()

    def test_no_alarm_when_disabled(self):
        with mock.patch.object(tqdm, '_play_alarm') as play:
            t, _ = self._bar(alarm=True, disable=True)
            t.update(3)
            t.close()
        play.assert_not_called()

    def test_no_alarm_when_bar_never_displayed(self):
        # delay suppresses display, so close() returns before the alarm
        with mock.patch.object(tqdm, '_play_alarm') as play:
            t, _ = self._bar(alarm=True, delay=10)
            t.update(3)
            t.close()
        play.assert_not_called()

    def test_alarm_rings_only_once_on_double_close(self):
        with mock.patch.object(tqdm, '_play_alarm') as play:
            t, _ = self._bar(alarm=True)
            t.update(3)
            t.close()
            t.close()
        play.assert_called_once_with()

    def test_play_alarm_uses_winsound_on_windows(self):
        fake_winsound = mock.MagicMock()
        t, _ = self._bar()
        with mock.patch.dict(sys.modules, {'winsound': fake_winsound}), \
                mock.patch.object(sys, 'platform', 'win32'):
            t._play_alarm()
        fake_winsound.Beep.assert_called_once_with(600, 300)
        t.close()

    def test_play_alarm_writes_bell_on_other_platforms(self):
        t, buf = self._bar()
        with mock.patch.object(sys, 'platform', 'linux'):
            t._play_alarm()
        self.assertIn('\a', buf.getvalue())
        t.close()

    def test_play_alarm_swallows_errors(self):
        # Setting the module to None makes `import winsound` raise ImportError
        t, _ = self._bar()
        with mock.patch.dict(sys.modules, {'winsound': None}), \
                mock.patch.object(sys, 'platform', 'win32'):
            t._play_alarm()  # must not raise
        t.close()


if __name__ == '__main__':
    unittest.main()