from wildcatting.table import format_row, format_separator, format_table


class TestFormatRow:
    def test_basic(self) -> None:
        assert format_row(["a", "bb", "ccc"], [3, 3, 3]) == "a   | bb  | ccc"

    def test_none_renders_as_empty(self) -> None:
        assert format_row([None, "x"], [3, 1]) == "    | x"

    def test_custom_sep(self) -> None:
        assert format_row(["a", "b"], [1, 1], sep=" , ") == "a , b"


class TestFormatSeparator:
    def test_produces_dashes(self) -> None:
        sep = format_separator([3, 5])
        assert "---" in sep
        assert "-----" in sep
        assert "-+-" in sep

    def test_width_matches_row(self) -> None:
        row = format_row(["ab", "cd"], [2, 2])
        sep = format_separator([2, 2])
        assert len(row) == len(sep)


class TestFormatTable:
    def test_header_and_rows(self) -> None:
        table = format_table(["Name", "Score"], [["alice", "100"], ["bob", "42"]])
        lines = table.splitlines()
        assert lines[0].startswith("Name")
        assert "Score" in lines[0]
        assert "alice" in lines[2]
        assert "bob" in lines[3]

    def test_none_row_produces_separator(self) -> None:
        table = format_table(["A", "B"], [["x", "y"], None, ["p", "q"]])
        lines = table.splitlines()
        # line 0: header, line 1: separator after header, line 2: first row,
        # line 3: separator for None row, line 4: last row
        assert all(c in "-+" for c in lines[3].replace(" ", ""))

    def test_column_widths_expand_to_fit_content(self) -> None:
        table = format_table(["X"], [["a very long value"]])
        assert "a very long value" in table

    def test_single_column(self) -> None:
        table = format_table(["Col"], [["val"]])
        assert "Col" in table
        assert "val" in table
