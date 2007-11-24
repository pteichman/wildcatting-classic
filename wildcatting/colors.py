import curses

class _Colors:
    """Semi-singleton for curses color setup"""
    _colors = {(curses.COLOR_WHITE, curses.COLOR_BLACK) : 0}

    def get(self, fg, bg):
        pair = (fg, bg)

        if not self._colors.has_key(pair):
            num = len(self._colors)
            curses.init_pair(num, fg, bg)
            self._colors[pair] = num

        return curses.color_pair(self._colors[pair])

Colors = _Colors()
