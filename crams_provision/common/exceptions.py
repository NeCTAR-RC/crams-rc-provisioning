class ProvisionException(Exception):
    """The base exception class for all exceptions this library raises.
    """
    pass


class AllocParseException(ProvisionException):
    """
    Allocation json parse exception
    """
    pass


class IdentifierException(ProvisionException):
    """
    tenant identifier exception
    """
    pass
