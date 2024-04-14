from click import ClickException


class ConfigurationError(ClickException):
    pass


class UsageError(ClickException):
    pass


class ConversionError(ClickException):
    pass
