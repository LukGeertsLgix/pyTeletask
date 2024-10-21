"""Module for Teletask Exceptions.

This module defines several custom exceptions for handling specific error
conditions in a Teletask system, such as failures to parse Teletask commands,
IP addresses, and more. Each exception provides detailed error reporting through
custom string representations and the ability to compare and hash exceptions.

Classes:
    - TeletaskException: The base class for all Teletask-related exceptions.
    - CouldNotParseTelegram: Raised when a Telegram (message) cannot be parsed.
    - CouldNotParseTeletaskCommand: Raised when there is an issue with the Teletask command.
    - CouldNotParseTeletaskIP: Raised for errors in parsing Teletask IP data.
    - ConversionError: Raised when type conversion fails.
    - CouldNotParseAddress: Raised for invalid address formats.
    - DeviceIllegalValue: Raised when an illegal value is set for a device.
"""

class TeletaskException(Exception):
    """Default Teletask Exception.

    This is the base class for all exceptions related to the Teletask system.
    It includes methods to compare exception instances and control their
    hashability.
    """

    def __eq__(self, other):
        """Override equality operator to compare based on attributes."""
        return self.__dict__ == other.__dict__

    def __hash__(self):
        """Override hash function to ensure consistent hash value."""
        return 0


class CouldNotParseTelegram(TeletaskException):
    """Exception raised when a Telegram message cannot be parsed.

    Attributes:
        description (str): The reason for the parsing failure.
        parameter (dict): Optional parameters providing more context about the failure.
    """

    def __init__(self, description, **kwargs):
        """Initialize CouldNotParseTelegram with a description and optional parameters.

        Args:
            description (str): Description of the error.
            kwargs: Additional parameters related to the error.
        """
        super(CouldNotParseTelegram, self).__init__("Could not parse Telegram")
        self.description = description
        self.parameter = kwargs

    def _format_parameter(self):
        """Format the parameters as a string for easier readability."""
        return " ".join(['%s="%s"' % (key, value) for (key, value) in sorted(self.parameter.items())])

    def __str__(self):
        """Return a string representation of the exception."""
        return '<CouldNotParseTelegram description="{0}" {1}/>' \
            .format(self.description, self._format_parameter())


class CouldNotParseTeletaskCommand(TeletaskException):
    """Exception raised when a Teletask command cannot be parsed.

    This error typically occurs when invalid or malformed data is encountered
    in a Teletask command.
    
    Attributes:
        description (str): Details of the parsing issue.
    """

    def __init__(self, description=""):
        """Initialize the exception with a description."""
        super(CouldNotParseTeletaskCommand, self).__init__("Could not parse Teletask Command")
        self.description = description

    def __str__(self):
        """Return a string representation of the exception."""
        return '<CouldNotParseTeletaskCommand description="{0}" />'.format(self.description)


class CouldNotParseTeletaskIP(TeletaskException):
    """Exception raised when Teletask IP data is invalid or incorrectly formatted.

    Attributes:
        description (str): Details about the parsing failure of the Teletask IP.
    """

    def __init__(self, description=""):
        """Initialize the exception with a description."""
        super(CouldNotParseTeletaskIP, self).__init__("Could not parse TeletaskIP")
        self.description = description

    def __str__(self):
        """Return a string representation of the exception."""
        return '<CouldNotParseTeletaskIP description="{0}" />'.format(self.description)


class ConversionError(TeletaskException):
    """Exception raised for errors during type conversions.

    Attributes:
        description (str): Description of the conversion failure.
        parameter (dict): Additional context about the error.
    """

    def __init__(self, description, **kwargs):
        """Initialize the exception with a description and optional parameters.

        Args:
            description (str): Explanation of the error.
            kwargs: Additional parameters related to the error.
        """
        super(ConversionError, self).__init__("Conversion Error")
        self.description = description
        self.parameter = kwargs

    def _format_parameter(self):
        """Format the parameters as a string for easier readability."""
        return " ".join(['%s="%s"' % (key, value) for (key, value) in sorted(self.parameter.items())])

    def __str__(self):
        """Return a string representation of the exception."""
        return '<ConversionError description="{0}" {1}/>'.format(self.description, self._format_parameter())


class CouldNotParseAddress(TeletaskException):
    """Exception raised for invalid address formats.

    Attributes:
        address (str): The address that caused the error.
    """

    def __init__(self, address=None):
        """Initialize the exception with the problematic address."""
        super(CouldNotParseAddress, self).__init__("Could not parse address")
        self.address = address

    def __str__(self):
        """Return a string representation of the exception."""
        return '<CouldNotParseAddress address="{0}" />'.format(self.address)


class DeviceIllegalValue(TeletaskException):
    """Exception raised when an illegal value is set for a device.

    Attributes:
        value (Any): The illegal value that was attempted.
        description (str): Description of why the value is illegal.
    """

    def __init__(self, value, description):
        """Initialize the exception with the value and a description."""
        super(DeviceIllegalValue, self).__init__("Illegal value for device")
        self.value = value
        self.description = description

    def __str__(self):
        """Return a string representation of the exception."""
        return '<DeviceIllegalValue description="{0}" value="{1}" />'.format(
            self.description, self.value)
