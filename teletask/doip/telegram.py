"""
Module for DoIP Telegrams.

This module defines classes and enums for handling Teletask DoIP (Digital over IP)
telegrams. Telegrams are the primary means of communication in Teletask systems,
and the module allows for constructing and representing these telegrams based
on various commands, functions, and settings.

Classes:
    - Telegram: Handles construction of DoIP telegrams.
    - TelegramHeartbeat: Manages the "keep-alive" telegrams for ongoing communication.

Enums:
    - TeletaskConst: Constants for Teletask system, such as START and CENTRAL identifiers.
    - TelegramCommand: Represents available Teletask commands (e.g., SET, GET).
    - TelegramFunction: Represents various functional units in the Teletask system.
    - TelegramSetting: Possible settings for functions (e.g., ON, OFF).
"""

from enum import Enum
from teletask.exceptions import CouldNotParseTeletaskCommand

class TeletaskConst(Enum):
    """Enum class for basic Teletask constants."""
    START = 2
    CENTRAL = 1


class TelegramCommand(Enum):
    """Enum class for Teletask command types."""
    SET = 7             # This command allows the CCT to set individual functions
    GET = 6             # When the TDS receives this command it reports the state of the specified device.
    GROUPGET = 9        # An extension of the Function Get. With this command it is possible to ask for the status of multiple devices of the same type at once
    LOG = 3             # When the TDS receives this command it (de-)activates it’s channel for reporting the function! Remark: If you have multiple connections to the TDS, the TDS keeps a list of functions which need to be reported for each connection.
    EVENTREPORT = 0x10  # TDS sends this command it the level of the specified load has changed (if the Function Log for this function on this connection has been set) , or as an answer to a Function Get (always)
    WRITEDISPLAY = 4    # This Command can be used to create a "Dynamic Message"
    KEEPALIVE = 11      # This command can be send to keep the socket open.


class TelegramFunction(Enum):
    """Enum class representing Teletask functional units."""
    RELAY = 1       # control or get the status of a relay
    DIMMER = 2      # control or get the status of a dimmer
    MOTOR = 6       # control or get the status of a Motor
    LOCMOOD = 8     # control or get the status of a Local Mood
    TIMEDMOOD = 9   # control or get the status of a Timed Local Mood
    GENMOOD = 10    # control or get the status of a General Mood
    FLAG = 15       # control or get the status of a Flag
    SENSOR = 20     # control or get the status of a Sensor zone
    AUDIO = 31      # control or get the status of a Audio zone
    PROCESS = 3     # control or get the status of a Process function
    REGIME = 14     # control or get the status of a Regime function
    TPKEY = 52      # simulate a key press on an interface
    SERVICE = 53    # control or get the status of a Service function
    MESSAGE = 54    # control or get the status of a Messages or Alarms
    CONDITION = 60  # get the status of a Condition


class TelegramSetting(Enum):
    """Enum class representing possible settings for Teletask units."""
    ON = 255
    TOGGLE = 103
    OFF = 0


class Telegram:
    """Class representing a Teletask DoIP telegram.

    This class is used to construct a Teletask telegram based on command,
    function, address, and setting parameters. It includes methods to generate
    the telegram string and calculate its length and checksum.
    
    Attributes:
        start (int): The start value of the telegram (from TeletaskConst.START).
        length (int): The length of the telegram.
        command (TelegramCommand): The telegram's command.
        payload (dict): The payload data for the telegram.
        checksum (int): The checksum value of the telegram.
    """

    def __init__(self, command=None, function=None, address=None, setting=None):
        """Initialize the Telegram instance.

        Args:
            command (TelegramCommand): The command type for the telegram (SET, GET, etc.).
            function (TelegramFunction): The functional unit involved in the command (RELAY, DIMMER, etc.).
            address (int): The address of the unit being targeted.
            setting (TelegramSetting): The setting to apply (ON, OFF, etc.).
        """
        self.start = TeletaskConst.START.value  # Start value from TeletaskConst
        self.length = 0  # Default length before calculation
        self.command = None  # Will be assigned a command value later
        self.payload = {}  # Dictionary to hold payload data

        # Logic for different command types
        if str(command) == "TelegramCommand.LOG":
            # Handle 'LOG' command (minimal payload)
            self.payload[0] = function.value #Fnc
            self.payload[1] = 1 # State
        elif str(command) == "TelegramCommand.GET":
            # Handle 'GET' command with additional parameters
            self.payload[0] = TeletaskConst.CENTRAL # Central address = 1
            self.payload[1] = function.value
            self.payload[2] = 0
            self.payload[3] = address
        elif str(command) == "TelegramCommand.SET":
            # Handle 'SET' command
            self.payload[0] = TeletaskConst.CENTRAL # Central address = 1 
            self.payload[1] = function.value if function else None
        else:
            # Raise an exception if the command is unrecognized
            raise CouldNotParseTeletaskCommand

        # Assign the command's value to the instance
        if command is not None:
            self.command = command.value

        # If a setting is provided, add it to the payload
        if setting is not None:
            self.payload[2] = 0  # Reserved value
            self.payload[3] = address
            self.payload[4] = setting.value

        self.checksum = 0  # Initialize checksum

    def to_teletask(self):
        """Generate the string representation of the telegram.

        This method calls the `__str__` method and prints the telegram.
        """
        print(str(self))
        return str(self)

    def __str__(self):
        """Generate a readable string for the telegram."""
        self.calc_length()  # Calculate length
        self.calc_checksum()  # Calculate checksum

        # Format the payload as a comma-separated string
        payload_str = ','.join(("{!s}".format(val) for (key, val) in self.payload.items()))
        message = "s,{0},{1},{2},{3},".format(self.length, self.command, payload_str, self.checksum)
        return message

    def __eq__(self, other):
        """Override equality operator to compare telegrams based on attributes."""
        return self.__dict__ == other.__dict__

    def calc_length(self):
        """Calculate the length of the telegram based on its payload."""
        try:
            self.length = len(self.payload) + 3  # 3 additional fields: start, command, checksum
        except Exception:
            # Default length if something goes wrong
            self.length = 8

    def calc_checksum(self):
        """Calculate the checksum for the telegram.

        The checksum is the sum of the payload values, start, length, and command,
        modulo 256.
        """
        packet_sum = sum(self.payload.values())  # Sum all payload values
        packet_sum += self.start + self.length + self.command  # Add start, length, and command
        self.checksum = packet_sum % 256  # Modulo 256


class TelegramHeartbeat:
    """Class for constructing heartbeat (keep-alive) telegrams.

    These telegrams are used to maintain active communication between the system
    and Teletask devices.
    
    Attributes:
        content (TelegramCommand): The keep-alive command.
    """

    def __init__(self):
        """Initialize the TelegramHeartbeat class."""
        self.content = TelegramCommand.KEEPALIVE  # Set command to KEEPALIVE

    def to_teletask(self):
        """Generate the string representation of the heartbeat telegram."""
        return str(self)

    def __str__(self):
        """Generate a readable string for the heartbeat telegram."""
        message = "s,3,{0},{1},".format(TelegramCommand.KEEPALIVE.value, (2 + 3 + 11) % 256)
        return message
