from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> dict:
        raise NotImplementedError