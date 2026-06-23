import curses
import logging
import platform

from wildcatting.colors import Colors


class View:
    log = logging.getLogger("Wildcatting")

    def __init__(self, stdscr: curses.window) -> None:
        self._stdscr = stdscr
        self._mac: bool = platform.system() == "Darwin"

    def get_green_fgbg(self) -> tuple[int, int]:
        color = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)
        return color, color

    def add_centered(
        self, win: curses.window, row: int, text: str, color: int | None = None
    ) -> None:
        (h, w) = win.getmaxyx()

        col = (w - len(text)) // 2
        if color is None:
            win.addstr(row, col, text)
        else:
            win.addstr(row, col, text, color)

    def add_left(
        self,
        win: curses.window,
        row: int,
        text: str,
        color: int | None = None,
        pad: int = 0,
    ) -> None:
        (h, w) = win.getmaxyx()

        col = pad
        if color is None:
            win.addstr(row, col, text)
        else:
            win.addstr(row, col, text, color)

    def add_right(
        self,
        win: curses.window,
        row: int,
        text: str,
        color: int | None = None,
        pad: int = 0,
    ) -> None:
        (h, w) = win.getmaxyx()

        col = w - len(text) - 1 - pad
        if color is None:
            win.addstr(row, col, text)
        else:
            win.addstr(row, col, text, color)

    def set_fgbg(self, win: curses.window, fg: int, bg: int) -> None:
        win.bkgdset(" ", fg)
        win.clear()

    def putch(
        self, win: curses.window, y: int, x: int, ch: int, attr: int | None = None
    ) -> None:
        # workaround so we can write things to the bottom corner
        # or otherwise with the same method call
        (h, w) = win.getmaxyx()
        f = win.insch if y == h - 1 and x == w - 1 else win.addch

        if attr:
            f(y, x, ch, attr)
        else:
            f(y, x, ch)
