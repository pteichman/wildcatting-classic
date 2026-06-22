import os
import sys
from gettext import gettext as _
from optparse import SUPPRESS_USAGE, OptionParser, Values
from typing import Any, NoReturn


class Command(OptionParser):
    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.name = name

        self.aliases: list[str] = kwargs.get("aliases", [])
        self.summary: str | None = kwargs.get("summary")

        for key in ("aliases", "summary"):
            if key in kwargs:
                del kwargs[key]

        OptionParser.__init__(self, *args, **kwargs)

        if len(self.aliases) > 0:
            self.helpstr = self.name + " ({})".format(", ".join(self.aliases))
        else:
            self.helpstr = self.name

    def get_prog_name(self) -> str:
        if self.prog is None:
            return os.path.basename(sys.argv[0])
        else:
            return self.prog

    def expand_cmd_name(self, s: str) -> str:
        return s.replace("%cmd", self.get_name())

    def expand_prog_name(self, s: str) -> str:
        return s.replace("%prog", self.get_prog_name())

    def set_usage(self, usage: str | None) -> None:
        if usage is None:
            self.usage = _("%prog %cmd [options]")
        elif usage is SUPPRESS_USAGE:
            self.usage = None
        else:
            self.usage = usage

    def get_usage(self) -> str:
        if self.usage:
            return self.formatter.format_usage(
                self.expand_cmd_name(self.expand_prog_name(self.usage))
            )
        else:
            return ""

    def has_name(self, alias: str | None) -> bool | None:
        if alias == self.name:
            return True
        if alias in self.aliases:
            return True
        return None

    def run(self, options: Values, args: list[str]) -> None:
        pass

    def get_name(self) -> str:
        return self.name

    def error(self, msg: str) -> NoReturn:
        # This is pretty nasty, but it's helpful to users.. rewrite
        # "no such option" error messages to include the command name.
        # I wonder how to add i18n properly here, so we'll match the
        # correct string everywhere

        s = "no such option: "
        if msg and msg.startswith(s):
            msg = _("no such %s option: %s") % (self.name, msg[len(s) :])
        self.exit(1, msg)

    def exit(self, status: int = 0, msg: str | None = None) -> NoReturn:
        if msg:
            sys.stderr.write(msg)
            sys.stderr.write("\n")
        sys.exit(status)


class CommandParser(OptionParser):
    """Parse command-line options CVS style."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "usage" not in kwargs:
            kwargs["usage"] = "%prog [options] <command> [command options]"
        OptionParser.__init__(self, *args, **kwargs)

        self.commands: list[Command] = []
        self.groups: dict[str, list[Command]] = {}

    def add_command(self, command: Command, group: str = "Other") -> None:
        self.commands.append(command)
        self.groups.setdefault(group, []).append(command)

    def find_command(self, alias: str) -> Command | None:
        for command in self.commands:
            if command.has_name(alias):
                return command
        return None

    def exit(self, status: int = 0, msg: str | None = None) -> NoReturn:
        if msg:
            sys.stderr.write(msg)
        sys.exit(status)

    def parse_args(  # type: ignore[override]
        self, *args: Any, **kwargs: Any
    ) -> tuple[Command | None, Values, list[str]]:
        self.disable_interspersed_args()
        (options, remaining) = OptionParser.parse_args(self, *args, **kwargs)

        cmd: Command | None = None

        if len(remaining) > 0:
            cmd = self.find_command(remaining[0])

            if cmd is None:
                self.print_unknown_command(remaining[0])
            else:
                (cmdoptions, remaining) = cmd.parse_args(remaining[1:])

                # update options with the values from cmdoptions
                for attr, val in list(cmdoptions.__dict__.items()):
                    setattr(options, attr, val)

        return (cmd, options, remaining)

    def print_unknown_command(self, cmdname: str, file: Any = None) -> None:
        if file is None:
            file = sys.stdout
        file.write(f"Unknown command '{cmdname}'\n")

    def format_help(self, *args: Any, **kwargs: Any) -> str:
        help = OptionParser.format_help(self, *args, **kwargs)
        return help + "\n" + self.format_command_help()

    def format_command_help(self) -> str:
        result = []

        groups = list(self.groups.keys())
        groups.sort()

        max_cmd_length = 0
        for cmd in self.commands:
            max_cmd_length = max(max_cmd_length, len(cmd.helpstr))

        for group in groups:
            result.append(f"{group} commands:\n")
            commands = self.groups[group]
            commands.sort(key=lambda x: x.get_name())

            for cmd in commands:
                padding = " " * (max_cmd_length - len(cmd.helpstr))
                result.append(f"  {cmd.helpstr}{padding}  {cmd.summary}\n")
        return "".join(result)
