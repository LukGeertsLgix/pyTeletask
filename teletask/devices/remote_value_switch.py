"""
Module for managing a DPT Switch remote value.
DPT 1.001.
"""

from enum import Enum
from .remote_value import RemoteValue  # Import base class for remote values
from teletask.doip import TelegramSetting  # Import the setting values for ON/OFF

class RemoteValueSwitch(RemoteValue):
    """Class to represent a remote value for switching (ON/OFF) in the Teletask system.
    
    This class handles the conversion between the raw values received from the Teletask
    system and a more abstract ON/OFF state, allowing easy management of a device's
    switch status.
    """

    class Value(Enum):
        """Enum for defining the ON and OFF values."""
        OFF = 0  # OFF state represented by 0
        ON = 255  # ON state represented by 255

    def __init__(self,
                 teletask,
                 group_address=None,
                 device_name=None,
                 after_update_cb=None,
                 doip_component=None,
                 invert=False):
        """Initialize the RemoteValueSwitch.

        Args:
            teletask: Teletask system instance managing the communication.
            group_address (str, optional): Group address where the switch is located.
            device_name (str, optional): Name of the device the switch controls.
            after_update_cb (function, optional): Callback to be called after updating the switch.
            doip_component (int, optional): DOIP component ID.
            invert (bool, optional): If True, inverts the ON/OFF logic.
        """
        super(RemoteValueSwitch, self).__init__(
            teletask, group_address,
            device_name=device_name, after_update_cb=after_update_cb,
            doip_component=doip_component)
        self.invert = invert  # Whether to invert the switch logic

    def to_teletask(self, value):
        """Convert the provided value to the payload format used by Teletask.

        Args:
            value (int): The value to be sent to the Teletask system, either ON or OFF.

        Returns:
            int: The value in Teletask payload format.
        """
        return value  # Directly return the value, no transformation needed

    def from_teletask(self, value):
        """Convert the payload received from Teletask to the switch state.

        Args:
            value (int): The value received from the Teletask system.

        Returns:
            int: The interpreted value (ON or OFF).
        """
        return value  # Return the received value as is

    async def off(self):
        """Set the switch to OFF state.

        Sends a command to turn off the switch.
        """
        await self.set(TelegramSetting.OFF.value)

    async def on(self):
        """Set the switch to ON state.

        Sends a command to turn on the switch.
        """
        await self.set(TelegramSetting.ON.value)
