from abc import ABC, abstractmethod
from argparse import Namespace, ArgumentParser


class ParserModule(ABC):
    @abstractmethod
    def init(self, parser: ArgumentParser):
        pass

    @abstractmethod
    def parser_name(self) -> str:
        pass

    @abstractmethod
    def process(self, ns: Namespace) -> str:
        pass