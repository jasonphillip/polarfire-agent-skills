class UnsupportedModelError(ValueError):
    """A Torch module cannot be transliterated by the selected adapter."""


class RemoteCommandError(RuntimeError):
    """A remote command failed; records retain its original diagnostics."""

    def __init__(self, message, records):
        super().__init__(message)
        self.records = records
