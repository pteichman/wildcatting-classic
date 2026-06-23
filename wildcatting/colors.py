import curses


class Colors:
    _colors: dict[tuple[int, int], int] = {(curses.COLOR_WHITE, curses.COLOR_BLACK): 0}

    @classmethod
    def get(cls, fg: int, bg: int) -> int:
        pair = (fg, bg)

        if pair not in cls._colors:
            num = len(cls._colors)
            curses.init_pair(num, fg, bg)
            cls._colors[pair] = num

        return curses.color_pair(cls._colors[pair])
