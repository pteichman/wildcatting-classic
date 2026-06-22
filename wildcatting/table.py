# some simple code for formatting text tables
from collections.abc import Sequence


def format_row(elts: Sequence[str | None], widths: list[int], sep: str = " | ") -> str:
    row = []
    for i in range(len(elts)):
        e = elts[i]
        elt = "" if e is None else e
        row.append(f"{elt:<{widths[i]}}")
    return sep.join(row)


def format_separator(widths: list[int]) -> str:
    elts = ["-" * width for width in widths]
    return format_row(elts, widths, "-+-")


def format_table(
    labels: Sequence[str], rows: Sequence[Sequence[str | None] | None]
) -> str:
    widths = [len(label) for label in labels]

    for row in rows:
        if row is not None:
            for i in range(len(row)):
                e = row[i]
                length = 0 if e is None else len(e)
                if length > widths[i]:
                    widths[i] = length

    table = []

    table.append(format_row(labels, widths).rstrip())
    table.append(format_separator(widths))

    for row in rows:
        if row is None:
            table.append(format_separator(widths))
        else:
            table.append(format_row(row, widths).rstrip())

    return "\n".join(table)
