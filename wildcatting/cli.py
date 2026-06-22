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


def main() -> None:
    parser = CommandParser()
    parser.add_argument("--debug", action="store_true", help="enable debugging output")
    parser.add_argument("--version", action="version", version=version.VERSION_STRING)

    parser.add_command(ClientCommand.ClientCommand())
    parser.add_command(ScreensaverCommand.ScreensaverCommand())
    parser.add_command(ServerCommand.ServerCommand())
    parser.add_command(PingCommand.ClientCommand())
    parser.add_command(ThemeInfoCommand.ThemeInfo())

    (command, options, args) = parser.parse_args()

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logging.root.addHandler(console)

    if options.debug:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.ERROR)

    if command is None:
        parser.print_help()
        sys.exit(1)

    try:
        command.run(options, args)
    except KeyboardInterrupt:
        print()
        sys.exit(1)
