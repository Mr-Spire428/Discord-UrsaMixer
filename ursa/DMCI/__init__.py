from argparse import ArgumentParser, ArgumentError, Namespace
from importlib import import_module
from os import listdir
from os.path import dirname, isfile, join, basename
from typing import Dict, Tuple, Optional, IO

from ..parser_module import ParserModule


PARSER_NAME: str = "Parser"
PARSER_PREFIX: str = "c!"


class __DEFUNCT_MODULE(ParserModule):
    def init(self, parser):
        return None

    def parser_name(self) -> str:
        return "DEFUNCT"

    def process(self, ns: Namespace) -> str:
        return "DEFUNCT MODULE: PARSE FAILED"


class DMCIArgumentParser(ArgumentParser):
    def error(self, message: str):
        raise ArgumentError(None, message)

    def exit(self, status: int = 0, message: Optional[str] = None):
        # This is only invoked by '-h','--help' action, so raise it as a message
        raise ArgumentError(None, self.format_help())

    def print_help(self, file: Optional[IO[str]] = None) -> None:
        # forget it
        pass


dmci_parser = DMCIArgumentParser(prog=PARSER_PREFIX)
dmci_subparsers = dmci_parser.add_subparsers(dest='module')

command_parsers: Dict[str, Tuple[ArgumentParser, ParserModule]] = dict()

IMPORTS_DIR = dirname(__file__)
for module in listdir(IMPORTS_DIR):
    print(f"DEBUG: probing module {module}...")
    if isfile(join(IMPORTS_DIR, module)) and module != basename(__file__):
        mod_name = '.'.join(['ursa', 'DMCI', module[:-3]])
        print(f"DEBUG: IMPORTING MODULE {mod_name}")
        mod = import_module(mod_name)
        parser_module: ParserModule = getattr(mod, PARSER_NAME, __DEFUNCT_MODULE)()
        if not isinstance(parser_module, ParserModule):
            parser_module = __DEFUNCT_MODULE()

        new_parser: ArgumentParser = dmci_subparsers.add_parser(parser_module.parser_name())
        parser_module.init(new_parser)
        command_parsers[parser_module.parser_name()] = (new_parser, parser_module)


def parse_command(command: str) -> Optional[str]:
    command = command.lstrip(PARSER_PREFIX).split()
    print(f"Parsers are: {command_parsers.keys()}")
    print(f"command is ({command})")
    try:
        ns = dmci_parser.parse_args(command)
    except ArgumentError as e:
        print(e.message)
        return e.message

    if ns.module:
        parse_mod: ParserModule = command_parsers.get(ns.module, (None, __DEFUNCT_MODULE()))[1]
        return parse_mod.process(ns)

    return dmci_parser.format_usage()
