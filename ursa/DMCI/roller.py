from argparse import Namespace, ArgumentParser
from random import randint

from ..parser_module import ParserModule


class Parser(ParserModule):
    parser: ArgumentParser

    def init(self, parser: ArgumentParser):
        self.parser = parser
        parser.add_argument('number', type=int, help="number of dice to roll")
        parser.add_argument('faces', type=int, help="number of faces per die")
        parser.add_argument('-m', '--modifier', type=int, default=0, help="modifier to add/subtract from dice result")

    def parser_name(self) -> str:
        return 'roll'

    def process(self, ns: Namespace) -> str:
        result = ""
        acc = 0
        for _ in range(ns.number):
            roll = randint(1, ns.faces)
            acc += roll
            result += f"Rolled a {roll}\n"

        result += '------\n'
        acc += ns.modifier
        result += f"Total: {acc}"
        return result
