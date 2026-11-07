from typing import Protocol


class ModelClient(Protocol):
    def complete(self, system: str, user: str) -> str:
        ...
