from typing import ClassVar, Any


class Symbol:
    """A constant symbol, nicer than ``object()``. Repeated calls return the
    same instance.

    >>> Symbol('foo') is Symbol('foo')
    True
    >>> Symbol('foo')
    foo
    """

    symbols: ClassVar[dict[str, "Symbol"]] = {}

    def __new__(cls, name: str) -> "Symbol":
        if name in cls.symbols:
            return cls.symbols[name]

        obj = super().__new__(cls)
        cls.symbols[name] = obj
        return obj

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def __getnewargs__(self) -> tuple[Any, ...]:
        return (self.name,)
