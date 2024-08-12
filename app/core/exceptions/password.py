from typing import Any


class InvalidPasswordException(Exception):
    def __init__(self, reason: Any) -> None:
        self.reason = reason
