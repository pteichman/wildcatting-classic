# some simple code for formatting text tables

def format_row(elts, widths, sep=" | "):
    import string
    
    row = []
    for i in range(len(elts)):
        if elts[i] is None:
            elt = ""
        else:
            elt = elts[i]

        row.append("%-*s" % (widths[i], elt))
    return string.join(row, sep)

def format_separator(widths):
    elts = [ "-" * width for width in widths ]
    return format_row(elts, widths, "-+-")

def format_table(labels, rows):
    widths = [ len(label) for label in labels ]

    for row in rows:
        if row is not None:
            for i in range(len(row)):
                if row[i] is None:
                    length = 0
                else:
                    length = len(row[i])

                if length > widths[i]: widths[i] = length

    table = []

    table.append(format_row(labels, widths).rstrip())
    table.append(format_separator(widths))

    for row in rows:
        if row is None:
            table.append(format_separator(widths))
        else:
            table.append(format_row(row, widths).rstrip())

    import string
    return string.join(table, "\n")
