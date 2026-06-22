import sys
from argparse import ArgumentParser, Namespace
from typing import Any


class Command(ArgumentParser):
    def __init__(self, name: str, **kwargs: Any) -> None:
        self.name = name
        self.aliases: list[str] = kwargs.pop("aliases", [])
        self.summary: str | None = kwargs.pop("summary", None)

        kwargs.setdefault("usage", f"%(prog)s {name} [options]")
        ArgumentParser.__init__(self, **kwargs)

        if self.aliases:
            self.helpstr = f"{name} ({', '.join(self.aliases)})"
        else:
            self.helpstr = name

    def has_name(self, alias: str | None) -> bool | None:
        if alias == self.name:
            return True
        if alias in self.aliases:
            return True
        return None

    def run(self, options: Namespace, args: list[str]) -> None:
        pass

    def get_name(self) -> str:
        return self.name


class CommandParser(ArgumentParser):
    """Parse command-line options CVS style."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("usage", "%(prog)s [options] <command> [command options]")
        ArgumentParser.__init__(self, **kwargs)

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

    def parse_args(  # type: ignore[override]
        self, args: list[str] | None = None
    ) -> tuple[Command | None, Namespace, list[str]]:
        options, remaining = ArgumentParser.parse_known_args(self, args)

        cmd: Command | None = None

        if remaining:
            cmd = self.find_command(remaining[0])

            if cmd is None:
                self.print_unknown_command(remaining[0])
            else:
                cmdoptions, remaining = cmd.parse_known_args(remaining[1:])
                vars(options).update(vars(cmdoptions))

        return cmd, options, remaining

    def print_unknown_command(self, cmdname: str, file: Any = None) -> None:
        if file is None:
            file = sys.stdout
        file.write(f"Unknown command '{cmdname}'\n")

    def format_help(self) -> str:
        return ArgumentParser.format_help(self) + "\n" + self.format_command_help()

    def format_command_help(self) -> str:
        result = []

        max_cmd_length = max((len(cmd.helpstr) for cmd in self.commands), default=0)

        for group in sorted(self.groups):
            result.append(f"{group} commands:\n")
            for cmd in sorted(self.groups[group], key=lambda x: x.get_name()):
                padding = " " * (max_cmd_length - len(cmd.helpstr))
                result.append(f"  {cmd.helpstr}{padding}  {cmd.summary}\n")

        return "".join(result)
