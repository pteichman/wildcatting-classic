import curses

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


class TestDrillKey:
    def testTimeout(self) -> None:
        assert _drill_key(-1) == DrillInput()

    def testQStops(self) -> None:
        assert _drill_key(ord("q")) == DrillInput(stop=True)

    def testUpperQStops(self) -> None:
        assert _drill_key(ord("Q")) == DrillInput(stop=True)

    def testAnyOtherKeyDrills(self) -> None:
        assert _drill_key(ord(" ")) == DrillInput(drill=True)
        assert _drill_key(ord("x")) == DrillInput(drill=True)
        assert _drill_key(curses.KEY_UP) == DrillInput(drill=True)


class TestWildcattingKey:
    def _key(
        self,
        c: int,
        x: int = 3,
        y: int = 3,
        fw: int = 10,
        fh: int = 10,
        mouse_pos: tuple[int, int] | None = None,
    ) -> tuple[int, int, WildcattingInput]:
        return _wildcatting_key(c, x, y, fw, fh, mouse_pos)

    def testTimeoutRequestsUpdate(self) -> None:
        x, y, action = self._key(-1)
        assert action == WildcattingInput(check_for_updates=True)
        assert (x, y) == (3, 3)

    def testArrowKeysMoveCursor(self) -> None:
        x, y, _ = self._key(curses.KEY_UP)
        assert (x, y) == (3, 2)

        x, y, _ = self._key(curses.KEY_DOWN)
        assert (x, y) == (3, 4)

        x, y, _ = self._key(curses.KEY_LEFT)
        assert (x, y) == (2, 3)

        x, y, _ = self._key(curses.KEY_RIGHT)
        assert (x, y) == (4, 3)

    def testMovementProducesNoAction(self) -> None:
        for key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            _, _, action = self._key(key)
            assert action == WildcattingInput()

    def testMovementClampsAtBoundary(self) -> None:
        x, y, _ = self._key(curses.KEY_UP, y=0)
        assert (x, y) == (3, 0)

        x, y, _ = self._key(curses.KEY_LEFT, x=0)
        assert (x, y) == (0, 3)

        x, y, _ = self._key(curses.KEY_DOWN, y=9)
        assert (x, y) == (3, 9)

        x, y, _ = self._key(curses.KEY_RIGHT, x=9)
        assert (x, y) == (9, 3)

    def testSpaceSurveysCurrentPosition(self) -> None:
        x, y, action = self._key(ord(" "))
        assert action == WildcattingInput(survey=(3, 3))
        assert (x, y) == (3, 3)

    def testEnterSurveysCurrentPosition(self) -> None:
        _, _, action = self._key(ord("\n"))
        assert action == WildcattingInput(survey=(3, 3))

    def testMouseSurveysTargetCell(self) -> None:
        # Field starts at screen offset (4, 2). Clicking screen pos (7, 5)
        # targets field cell (3, 3) from cursor (3, 3) — dx=0, dy=0.
        x, y, action = self._key(curses.KEY_MOUSE, mouse_pos=(7, 5))
        assert (x, y) == (3, 3)
        assert action == WildcattingInput(survey=(3, 3))

    def testMouseMovesAndSurveys(self) -> None:
        # Clicking screen pos (8, 5) from cursor (3, 3): dx=1, dy=0 → (4, 3).
        x, y, action = self._key(curses.KEY_MOUSE, mouse_pos=(8, 5))
        assert (x, y) == (4, 3)
        assert action == WildcattingInput(survey=(3, 4))

    def testMouseOutOfBoundsProducesNoAction(self) -> None:
        x, y, action = self._key(curses.KEY_MOUSE, mouse_pos=(100, 100))
        assert (x, y) == (3, 3)
        assert action == WildcattingInput()

    def testUnknownKeyProducesNoAction(self) -> None:
        x, y, action = self._key(ord("z"))
        assert (x, y) == (3, 3)
        assert action == WildcattingInput()


class TestReportNavigate:
    def _nav(
        self, c: int, turn: int | None = None, page: int = 0, week: int = 13
    ) -> _ReportCursor:
        return _report_navigate(c, _ReportCursor(turn=turn, page=page), week)

    def testUpFromNextPlayerMovesToLastTurnOnPage(self) -> None:
        assert self._nav(curses.KEY_UP, turn=None, page=0, week=5) == _ReportCursor(
            turn=5, page=0
        )

    def testUpClampedAtTopOfPage(self) -> None:
        assert self._nav(curses.KEY_UP, turn=1, page=0, week=13) == _ReportCursor(
            turn=1, page=0
        )

    def testUpClampedAtTopOfSecondPage(self) -> None:
        assert self._nav(curses.KEY_UP, turn=14, page=1, week=26) == _ReportCursor(
            turn=14, page=1
        )

    def testUpMovesCursor(self) -> None:
        assert self._nav(curses.KEY_UP, turn=5, page=0, week=13) == _ReportCursor(
            turn=4, page=0
        )

    def testDownFromLastTurnGoesToNextPlayer(self) -> None:
        assert self._nav(curses.KEY_DOWN, turn=5, page=0, week=5) == _ReportCursor(
            turn=None, page=0
        )

    def testDownFromNextPlayerDoesNothing(self) -> None:
        assert self._nav(curses.KEY_DOWN, turn=None, page=0, week=13) == _ReportCursor(
            turn=None, page=0
        )

    def testDownMovesCursor(self) -> None:
        assert self._nav(curses.KEY_DOWN, turn=3, page=0, week=13) == _ReportCursor(
            turn=4, page=0
        )

    def testPpageDecrementsPage(self) -> None:
        assert self._nav(curses.KEY_PPAGE, turn=15, page=1, week=26) == _ReportCursor(
            turn=None, page=0
        )

    def testPpageAtFirstPageDoesNothing(self) -> None:
        assert self._nav(curses.KEY_PPAGE, turn=3, page=0, week=13) == _ReportCursor(
            turn=3, page=0
        )

    def testNpageIncrementsPage(self) -> None:
        assert self._nav(curses.KEY_NPAGE, turn=3, page=0, week=26) == _ReportCursor(
            turn=None, page=1
        )

    def testNpageAtLastPageDoesNothing(self) -> None:
        assert self._nav(curses.KEY_NPAGE, turn=3, page=0, week=13) == _ReportCursor(
            turn=3, page=0
        )

    def testActionKeyDoesNotNavigate(self) -> None:
        assert self._nav(ord(" "), turn=3, page=0, week=13) == _ReportCursor(
            turn=3, page=0
        )


class TestReportAction:
    def setup_method(self) -> None:
        self.report_dict = {
            3: {"row": 2, "col": 4},
            5: {"row": 7, "col": 1},
        }

    def testSpaceAtNextPlayerAdvances(self) -> None:
        assert _report_action(ord(" "), None, self.report_dict) == ReportInput(
            next_player=True
        )

    def testEnterAtNextPlayerAdvances(self) -> None:
        assert _report_action(ord("\n"), None, self.report_dict) == ReportInput(
            next_player=True
        )

    def testSpaceOnSurveyedTurnSells(self) -> None:
        assert _report_action(ord(" "), 3, self.report_dict) == ReportInput(sell=(2, 4))

    def testSpaceOnUnsurveyedTurnDoesNothing(self) -> None:
        assert _report_action(ord(" "), 4, self.report_dict) == ReportInput()

    def testNavigationKeysProduceNoAction(self) -> None:
        for key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_PPAGE, curses.KEY_NPAGE):
            assert _report_action(key, 3, self.report_dict) == ReportInput()

    def testTimeoutProducesNoAction(self) -> None:
        assert _report_action(-1, None, self.report_dict) == ReportInput()
