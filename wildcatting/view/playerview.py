import curses
import curses.textpad
import time
from typing import Any

from .view import View


class PlayerCountView(View):
    def __init__(self, stdscr: Any) -> None:
        View.__init__(self, stdscr)

        (h, w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h - 16) // 2, (w - 48) // 2)

    def display(self, gameFinished: bool = False) -> None:
        self._stdscr.clear()
        self._stdscr.refresh()

        fg, bg = self.get_green_fgbg()
        self.setFGBG(self._win, fg, bg)

        self.addCentered(self._win, 1, "WILDCATTING")
        self.addCentered(self._win, 3, "HOW MANY PLAYERS? (1-4) ")

        self._win.refresh()

    def input(self) -> int:
        while True:
            c = self._stdscr.getch()

            try:
                num = int(chr(c))
                if 0 < num < 5:
                    return num
            except Exception:
                pass

            self.addCentered(self._win, 13, "INVALID INPUT")
            self._win.refresh()
            time.sleep(1.0)
            self.display()


class PlayerNamesView(View):
    def __init__(self, stdscr: Any, count: int) -> None:
        View.__init__(self, stdscr)

        self._count = count
        self._textpads: list[Any] = []

        (h, w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h - 16) // 2, (w - 48) // 2)

    def display(self, gameFinished: bool = False) -> None:
        self._stdscr.clear()
        self._stdscr.refresh()
        (h, w) = self._win.getmaxyx()

        fg, bg = self.get_green_fgbg()
        self.setFGBG(self._win, fg, bg)

        self.addCentered(self._win, 1, "PLAYERS")

        for i in range(1, self._count + 1):
            row = i * 2 + 1
            self.addLeft(self._win, row, f"{i}. ", pad=10)

            # name field
            name_w = w - 13 * 2 - 3
            win = self._win.derwin(1, name_w, row, 13)
            textpad = curses.textpad.Textbox(win)
            self._textpads.append(textpad)

            # symbol field
            win = self._win.derwin(1, 2, row, 13 + name_w + 3)
            textpad = curses.textpad.Textbox(win)
            self._textpads.append(textpad)

        self._win.refresh()

    def input(self) -> list[tuple[str, str]]:
        players: list[tuple[str, str]] = []
        for i in range(self._count):
            nameField = self._textpads[2 * i]
            symbolField = self._textpads[2 * i + 1]

            nameField.edit()
            name = nameField.gather().strip()

            defaultSymbol = name[0].upper()

            symbolField.win.addch(0, 0, defaultSymbol)
            symbolField.edit()
            symbol = symbolField.gather().strip()

            # mac workaround.. we have hidden dots all over the screen
            name = name.strip(".")
            symbol = symbol.strip(".")

            if len(symbol) == 0:
                symbol = defaultSymbol

            players.append((name, symbol))

        return players


if __name__ == "__main__":
    names = None

    def main(stdscr: Any) -> None:
        countView = PlayerCountView(stdscr)
        countView.display()

        count = countView.input()

        namesView = PlayerNamesView(stdscr, count)
        namesView.display()

        global names
        names = namesView.input()

    curses.wrapper(main)
    print(names)
