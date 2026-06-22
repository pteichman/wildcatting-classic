import curses
import unittest

from wildcatting.view.reportview import (
    ReportInput,
    _report_action,
    _report_navigate,
    _ReportCursor,
)
from wildcatting.view.wildcattingview import (
    DrillInput,
    WildcattingInput,
    _drill_key,
    _wildcatting_key,
)


class TestDrillKey(unittest.TestCase):
    def testTimeout(self):
        self.assertEqual(_drill_key(-1), DrillInput())

    def testQStops(self):
        self.assertEqual(_drill_key(ord("q")), DrillInput(stop=True))

    def testUpperQStops(self):
        self.assertEqual(_drill_key(ord("Q")), DrillInput(stop=True))

    def testAnyOtherKeyDrills(self):
        self.assertEqual(_drill_key(ord(" ")), DrillInput(drill=True))
        self.assertEqual(_drill_key(ord("x")), DrillInput(drill=True))
        self.assertEqual(_drill_key(curses.KEY_UP), DrillInput(drill=True))


class TestWildcattingKey(unittest.TestCase):
    def _key(self, c, x=3, y=3, fw=10, fh=10, mouse_pos=None):
        return _wildcatting_key(c, x, y, fw, fh, mouse_pos)

    def testTimeoutRequestsUpdate(self):
        x, y, action = self._key(-1)
        self.assertEqual(action, WildcattingInput(check_for_updates=True))
        self.assertEqual((x, y), (3, 3))

    def testArrowKeysMoveCursor(self):
        x, y, _ = self._key(curses.KEY_UP)
        self.assertEqual((x, y), (3, 2))

        x, y, _ = self._key(curses.KEY_DOWN)
        self.assertEqual((x, y), (3, 4))

        x, y, _ = self._key(curses.KEY_LEFT)
        self.assertEqual((x, y), (2, 3))

        x, y, _ = self._key(curses.KEY_RIGHT)
        self.assertEqual((x, y), (4, 3))

    def testMovementProducesNoAction(self):
        for key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            with self.subTest(key=key):
                _, _, action = self._key(key)
                self.assertEqual(action, WildcattingInput())

    def testMovementClampsAtBoundary(self):
        x, y, _ = self._key(curses.KEY_UP, y=0)
        self.assertEqual((x, y), (3, 0))

        x, y, _ = self._key(curses.KEY_LEFT, x=0)
        self.assertEqual((x, y), (0, 3))

        x, y, _ = self._key(curses.KEY_DOWN, y=9)
        self.assertEqual((x, y), (3, 9))

        x, y, _ = self._key(curses.KEY_RIGHT, x=9)
        self.assertEqual((x, y), (9, 3))

    def testSpaceSurveysCurrentPosition(self):
        x, y, action = self._key(ord(" "))
        self.assertEqual(action, WildcattingInput(survey=(3, 3)))
        self.assertEqual((x, y), (3, 3))

    def testEnterSurveysCurrentPosition(self):
        _, _, action = self._key(ord("\n"))
        self.assertEqual(action, WildcattingInput(survey=(3, 3)))

    def testMouseSurveysTargetCell(self):
        # Field starts at screen offset (4, 2). Clicking screen pos (7, 5)
        # targets field cell (3, 3) from cursor (3, 3) — dx=0, dy=0.
        x, y, action = self._key(curses.KEY_MOUSE, mouse_pos=(7, 5))
        self.assertEqual((x, y), (3, 3))
        self.assertEqual(action, WildcattingInput(survey=(3, 3)))

    def testMouseMovesAndSurveys(self):
        # Clicking screen pos (8, 5) from cursor (3, 3): dx=1, dy=0 → (4, 3).
        x, y, action = self._key(curses.KEY_MOUSE, mouse_pos=(8, 5))
        self.assertEqual((x, y), (4, 3))
        self.assertEqual(action, WildcattingInput(survey=(3, 4)))

    def testMouseOutOfBoundsProducesNoAction(self):
        x, y, action = self._key(curses.KEY_MOUSE, mouse_pos=(100, 100))
        self.assertEqual((x, y), (3, 3))
        self.assertEqual(action, WildcattingInput())

    def testUnknownKeyProducesNoAction(self):
        x, y, action = self._key(ord("z"))
        self.assertEqual((x, y), (3, 3))
        self.assertEqual(action, WildcattingInput())


class TestReportNavigate(unittest.TestCase):
    def _nav(self, c, turn=None, page=0, week=13):
        return _report_navigate(c, _ReportCursor(turn=turn, page=page), week)

    def testUpFromNextPlayerMovesToLastTurnOnPage(self):
        self.assertEqual(
            self._nav(curses.KEY_UP, turn=None, page=0, week=5),
            _ReportCursor(turn=5, page=0),
        )

    def testUpClampedAtTopOfPage(self):
        self.assertEqual(
            self._nav(curses.KEY_UP, turn=1, page=0, week=13),
            _ReportCursor(turn=1, page=0),
        )

    def testUpClampedAtTopOfSecondPage(self):
        self.assertEqual(
            self._nav(curses.KEY_UP, turn=14, page=1, week=26),
            _ReportCursor(turn=14, page=1),
        )

    def testUpMovesCursor(self):
        self.assertEqual(
            self._nav(curses.KEY_UP, turn=5, page=0, week=13),
            _ReportCursor(turn=4, page=0),
        )

    def testDownFromLastTurnGoesToNextPlayer(self):
        self.assertEqual(
            self._nav(curses.KEY_DOWN, turn=5, page=0, week=5),
            _ReportCursor(turn=None, page=0),
        )

    def testDownFromNextPlayerDoesNothing(self):
        self.assertEqual(
            self._nav(curses.KEY_DOWN, turn=None, page=0, week=13),
            _ReportCursor(turn=None, page=0),
        )

    def testDownMovesCursor(self):
        self.assertEqual(
            self._nav(curses.KEY_DOWN, turn=3, page=0, week=13),
            _ReportCursor(turn=4, page=0),
        )

    def testPpageDecrementsPage(self):
        self.assertEqual(
            self._nav(curses.KEY_PPAGE, turn=15, page=1, week=26),
            _ReportCursor(turn=None, page=0),
        )

    def testPpageAtFirstPageDoesNothing(self):
        self.assertEqual(
            self._nav(curses.KEY_PPAGE, turn=3, page=0, week=13),
            _ReportCursor(turn=3, page=0),
        )

    def testNpageIncrementsPage(self):
        self.assertEqual(
            self._nav(curses.KEY_NPAGE, turn=3, page=0, week=26),
            _ReportCursor(turn=None, page=1),
        )

    def testNpageAtLastPageDoesNothing(self):
        self.assertEqual(
            self._nav(curses.KEY_NPAGE, turn=3, page=0, week=13),
            _ReportCursor(turn=3, page=0),
        )

    def testActionKeyDoesNotNavigate(self):
        self.assertEqual(
            self._nav(ord(" "), turn=3, page=0, week=13),
            _ReportCursor(turn=3, page=0),
        )


class TestReportAction(unittest.TestCase):
    def setUp(self):
        self.report_dict = {
            3: {"row": 2, "col": 4},
            5: {"row": 7, "col": 1},
        }

    def testSpaceAtNextPlayerAdvances(self):
        self.assertEqual(
            _report_action(ord(" "), None, self.report_dict),
            ReportInput(next_player=True),
        )

    def testEnterAtNextPlayerAdvances(self):
        self.assertEqual(
            _report_action(ord("\n"), None, self.report_dict),
            ReportInput(next_player=True),
        )

    def testSpaceOnSurveyedTurnSells(self):
        self.assertEqual(
            _report_action(ord(" "), 3, self.report_dict),
            ReportInput(sell=(2, 4)),
        )

    def testSpaceOnUnsurveyedTurnDoesNothing(self):
        self.assertEqual(
            _report_action(ord(" "), 4, self.report_dict),
            ReportInput(),
        )

    def testNavigationKeysProduceNoAction(self):
        for key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_PPAGE, curses.KEY_NPAGE):
            with self.subTest(key=key):
                self.assertEqual(
                    _report_action(key, 3, self.report_dict),
                    ReportInput(),
                )

    def testTimeoutProducesNoAction(self):
        self.assertEqual(
            _report_action(-1, None, self.report_dict),
            ReportInput(),
        )


if __name__ == "__main__":
    unittest.main()
