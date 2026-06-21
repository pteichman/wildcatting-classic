import logging
import sys

from wildcatting import (
    ClientCommand,
    PingCommand,
    ScreensaverCommand,
    ServerCommand,
    ThemeInfoCommand,
    version,
)
from wildcatting.cmdparse import CommandParser


def main():
    parser = CommandParser()
    parser.add_option(
        "", "--debug", action="store_true", help="enable debugging output"
    )
    parser.add_option(
        "", "--version", action="store_true", help="print the version and exit"
    )

    parser.add_commands(ClientCommand)
    parser.add_commands(ScreensaverCommand)
    parser.add_commands(ServerCommand)
    parser.add_commands(PingCommand)
    parser.add_commands(ThemeInfoCommand)

    (command, options, args) = parser.parse_args()

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logging.root.addHandler(console)

    if options.debug:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.ERROR)

    if options.version:
        print(version.VERSION_STRING)
        sys.exit(0)

    if command is None:
        parser.print_help()
        sys.exit(1)

    try:
        command.run(options, args)
    except KeyboardInterrupt:
        print()
        sys.exit(1)
