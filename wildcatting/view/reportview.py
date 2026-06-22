import curses
import logging
from dataclasses import dataclass
from typing import Any

from .oilfieldview import ProbabilityColorChooser
from .view import View


@dataclass
class ReportInput:
    next_player: bool = False
    sell: tuple[int, int] | None = None


@dataclass
class _ReportCursor:
    turn: int | None = None
    page: int = 0


def _report_navigate(c: int, cursor: _ReportCursor, week: int) -> _ReportCursor:
    turn, page = cursor.turn, cursor.page
    if c == curses.KEY_UP:
        if turn is None:
            turn = min(week, 13 * (page + 1))
        elif turn - (page * 13) > 1:
            turn -= 1
    elif c == curses.KEY_DOWN:
        if turn is not None:
            if turn == min(week, 13 * (page + 1)):
                turn = None
            else:
                turn += 1
    elif c == curses.KEY_PPAGE:
        if page > 0:
            page -= 1
            turn = None
    elif c == curses.KEY_NPAGE:
        if page < (week - 1) // 13:
            page += 1
            turn = None
    return _ReportCursor(turn=turn, page=page)


def _report_action(c: int, cursor_turn: int | None, report_dict: dict) -> ReportInput:
    if c == ord(" ") or c == ord("\n"):
        if cursor_turn is None:
            return ReportInput(next_player=True)
        if cursor_turn in report_dict:
            row_dict = report_dict[cursor_turn]
            return ReportInput(sell=(row_dict["row"], row_dict["col"]))
    return ReportInput()


class WeeklySummaryView(View):
    def __init__(self, stdscr: Any, report: Any) -> None:
        View.__init__(self, stdscr)

        self._report = report

        (h, w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h - 16) // 2, (w - 48) // 2)

    def display(self, gameFinished: bool = False) -> None:
        self._stdscr.clear()
        self._stdscr.refresh()

        fg, bg = self.get_green_fgbg()
        self.setFGBG(self._win, fg, bg)

        self.addCentered(self._win, 1, "... WILDCATTING ...")
        if not gameFinished:
            self.addCentered(self._win, 3, f"WEEK {self._report.week!s:>3}")
        else:
            self.addCentered(self._win, 3, "FINAL REPORT")
        row = 6
        reportRows = self._report.report_rows
        for rowDict in reportRows:
            username = rowDict["username"]
            profitAndLoss = rowDict["profitAndLoss"]
            leader = rowDict["leader"]
            if leader:
                self.addLeft(self._win, row, "*", pad=10)
            self.addLeft(self._win, row, username, pad=12)

            # could be profit, but probably a loss
            loss = f"$ {profitAndLoss:8d}"

            self.addRight(self._win, row, loss, pad=12)

            # support up to 9 or more players
            if len(reportRows) > 5:
                row += 1
            else:
                row += 2

        self._win.refresh()

    def input(self) -> bool:
        return bool(self._stdscr.getch() != -1)


class WeeklyReportView(View):
    log = logging.getLogger("Wildcatting")

    def __init__(self, stdscr: Any, report: Any, field: Any) -> None:
        View.__init__(self, stdscr)

        self._report = report
        self._field = field

        (h, w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h - 16) // 2, (w - 48) // 2)
        self._colorChooser = ProbabilityColorChooser()

        self._cursor = _ReportCursor(page=(report.week - 1) // 13)

    def set_report(self, report: Any) -> None:
        self._report = report

    def set_field(self, field: Any) -> None:
        self._field = field

    def display(self) -> None:
        self._stdscr.clear()
        self._stdscr.refresh()
        (h, w) = self._win.getmaxyx()

        fg, bg = self.get_green_fgbg()
        self.setFGBG(self._win, fg, bg)

        self._win.addstr(0, 0, self._report.username.upper())
        self.addCentered(self._win, 0, f"{self._report.oil_price} PER BARREL")
        self.addRight(self._win, 0, f"WEEK {self._report.week}")
        self._win.addstr(1, 1, "  X   Y   COST     TAX     INCOME     P&L")

        week = self._report.week
        reportDict = self._report.report_dict
        page = self._cursor.page
        lastWeekOnPage = min(week, 13 * (page + 1))
        for turn in range((page * 13) + 1, lastWeekOnPage + 1):
            if turn in reportDict:
                rowDict = reportDict[turn]
                row = rowDict["row"]
                col = rowDict["col"]
                site = self._field.get_site(row, col)
                if site.well.sold:
                    symbol = " "
                else:
                    symbol = self._report.symbol
                self._win.addstr(
                    turn - (page * 13) + 1,
                    0,
                    symbol,
                    self._colorChooser.site_color(site),
                )
            else:
                rowDict = {
                    "row": 0,
                    "col": 0,
                    "cost": 0,
                    "tax": 0,
                    "income": 0,
                    "profitAndLoss": 0,
                }

            col = rowDict["col"]
            row_num = rowDict["row"]
            cost = rowDict["cost"]
            tax = rowDict["tax"]
            income = rowDict["income"]
            pl = rowDict["profitAndLoss"]
            well_str = (
                f" {col!s:>2} {row_num!s:>3}   ${cost!s:>4}    ${tax!s:>4}"
                f"   ${income!s:>4}      ${pl!s:>7}"
            )
            self._win.addstr(turn - (page * 13) + 1, 1, well_str)

        self._win.addstr(15, 0, " NEXT PLAYER")
        if page == (self._report.week - 1) // 13:
            pl = str(self._report.profit_and_loss).rjust(10)
            self._win.addstr(15, 35, f"$ {pl}")
        self._move_cursor()
        self._win.refresh()

    def _move_cursor(self) -> None:
        turn, page = self._cursor.turn, self._cursor.page
        row = 15 if turn is None else turn - (page * 13) + 1
        self._win.move(row, 0)

    def _input(self) -> ReportInput:
        self._move_cursor()
        c = self._stdscr.getch()

        old = self._cursor
        self._cursor = _report_navigate(c, self._cursor, self._report.week)
        action = _report_action(c, old.turn, self._report.report_dict)

        if self._cursor.page != old.page:
            self.display()
        elif self._cursor != old:
            self._move_cursor()

        self._win.refresh()
        return action

    def input(self) -> ReportInput:
        curses.cbreak()
        try:
            return self._input()
        finally:
            curses.halfdelay(50)


class SurveyorsReportView(View):
    def __init__(self, stdscr: Any, site: Any, surveyed: bool) -> None:
        View.__init__(self, stdscr)

        self._site = site
        self._surveyed = surveyed
        (h, w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h - 16) // 2, (w - 48) // 2)

    def display(self) -> None:
        self._stdscr.clear()
        self._stdscr.refresh()

        (h, w) = self._win.getmaxyx()
        coord_str = f"X={self._site.col}  Y={self._site.row}"
        prob_str = str(self._site.probability).rjust(2) + "%"
        cost_str = "$" + str(self._site.drill_cost).rjust(4)
        tax_str = "$" + str(self._site.tax).rjust(4)

        fg, bg = self.get_green_fgbg()
        self.setFGBG(self._win, fg, bg)

        self._win.addstr(1, 14, "SURVEYOR'S REPORT")
        self._win.addstr(4, 12, "LOCATION")
        self._win.addstr(4, 24, coord_str)
        self._win.addstr(6, 12, "PROBABILITY OF OIL")
        self._win.addstr(6, 31, prob_str)
        self._win.addstr(8, 12, "COST PER METER")
        self._win.addstr(8, 29, cost_str)
        self._win.addstr(10, 12, "TAXES PER WEEK")
        self._win.addstr(10, 29, tax_str)

        if not self._surveyed:
            self._win.addstr(15, 13, "DRILL A WELL? (Y-N) ")
        else:
            self._win.addstr(15, 16, "PRESS ANY KEY")

        self._win.refresh()

    def input(self) -> bool:
        (h, w) = self._stdscr.getmaxyx()
        (wh, ww) = self._win.getmaxyx()
        done = False
        cur = "n"
        self._win.keypad(1)
        self._win.move(15, 30)
        self._win.refresh()
        curses.mousemask(curses.BUTTON1_CLICKED)
        curses.curs_set(1)
        while not done:
            c = self._win.getch()
            if self._surveyed:
                break

            if c == curses.KEY_UP or c == curses.KEY_LEFT:
                cur = "y"
            elif c == curses.KEY_DOWN or c == curses.KEY_RIGHT:
                cur = "n"
            elif c == ord("y"):
                cur = "y"
                done = True
            elif c == ord("n"):
                cur = "n"
                done = True
            elif (c == ord(" ")) or (c == 10):
                done = True
            elif c == curses.KEY_MOUSE:
                mid, mx, my, mz, bstate = curses.getmouse()
                x = mx - (w - ww) // 2
                y = my - (h - wh) // 2

                if y == 15 and x == 28:
                    cur = "y"
                    done = True
                if y == 15 and x == 30:
                    cur = "n"
                    done = True

            if cur == "y":
                self._win.move(15, 28)
            else:
                self._win.move(15, 30)

            self._win.refresh()

        return cur == "y"


class PregameReportView(View):
    log = logging.getLogger("Wildcatting")

    def __init__(
        self, stdscr: Any, gameId: str, isMaster: bool, players: list[str]
    ) -> None:
        View.__init__(self, stdscr)

        self._gameId = gameId
        self._isMaster = isMaster
        self._players = players

        (h, w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h - 16) // 2, (w - 48) // 2)

    def display(self) -> None:
        self._stdscr.clear()
        self._stdscr.refresh()

        (h, w) = self._win.getmaxyx()

        fg, bg = self.get_green_fgbg()
        self.setFGBG(self._win, fg, bg)

        self.addCentered(self._win, 1, f"PLAYERS: GAME {self._gameId}")

        row = 3
        for player in self._players:
            self._win.addstr(row, 2, player)
            row = row + 1

        if self._isMaster:
            self.addCentered(self._win, h - 1, "ANY KEY TO START")

        self._win.refresh()

    def input(self) -> bool:
        (h, w) = self._stdscr.getmaxyx()
        (wh, ww) = self._win.getmaxyx()

        # We're getting two clicks here somehow, disabling mouse for now
        # curses.mousemask(curses.BUTTON1_DOUBLE_CLICKED)

        try:
            try:
                curses.halfdelay(50)
                c = self._win.getch()

                # the docs claim that an exception is thrown if the halfdelay()
                # timeout is hit, but in practice it seems to return -1 instead
                if c == -1:
                    return False
            except KeyboardInterrupt:
                raise
            except Exception:
                return False
        finally:
            curses.cbreak()

        return True
