"""
Module for managing a Scaling remote value (Dimmer control).
DPT 5.001 (Dimmer percentage control).
"""
from .remote_value import RemoteValue


class RemoteValueScaling(RemoteValue):
    """
    Class for managing the scaling remote value of a dimmer in the Teletask system.
    
    This class allows for controlling the dimming value (brightness) of a device,
    by converting between a percentage value and the Teletask system's internal format.
    """

    def __init__(self, 
                 teletask, 
                 group_address=None, 
                 device_name=None, 
                 after_update_cb=None, 
                 range_from=100, 
                 range_to=0, 
                 doip_component="DIMMER"):
        """
        Initialize the RemoteValueScaling class for managing dimmer values.

        Args:
            teletask: The main Teletask system reference.
            group_address: The Teletask group address associated with the dimmer.
            device_name: The name of the dimmer device.
            after_update_cb: Callback function to execute after value updates.
            range_from: The upper limit of the dimming range (default: 100).
            range_to: The lower limit of the dimming range (default: 0).
            doip_component: The Teletask component type (default: "DIMMER").
        """
        super(RemoteValueScaling, self).__init__(
            teletask, 
            group_address=group_address, 
            device_name=device_name, 
            after_update_cb=after_update_cb, 
            doip_component=doip_component)

        # Upper and lower limits for the dimming range (default is 0-100%)
        self.range_from = range_from
        self.range_to = range_to

    def to_teletask(self, value):
        """
        Convert the given value (percentage) into a payload for the Teletask system.

        Args:
            value: The value to be converted (typically a percentage).

        Returns:
            The converted value ready to be sent to the Teletask system.
        """
        return value

    def from_teletask(self, value):
        """
        Convert a received payload from the Teletask system into a usable value (percentage).

        Args:
            value: The raw payload received from Teletask.

        Returns:
            The converted value as a percentage (from 0 to 100).
        """
        return value

    @property
    def unit_of_measurement(self):
        """
        Return the unit of measurement for the dimmer value.

        Returns:
            str: The unit of measurement (percentage: "%").
        """
        return "%"
