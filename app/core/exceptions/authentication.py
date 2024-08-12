class TransportLogoutNotSupportedError(Exception):
    pass


class StrategyDestroyNotSupportedError(Exception):
    pass


class JWTStrategyDestroyNotSupportedError(StrategyDestroyNotSupportedError):
    def __init__(self) -> None:
        message = "A JWT can't be invalidated: it's valid until it expires."
        super().__init__(message)


class DuplicateBackendNamesError(Exception):
    pass


class BackendNotFoundError(Exception):
    pass
