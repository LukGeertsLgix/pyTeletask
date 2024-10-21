"""
Module for managing a Switch via Teletask.
It provides functionality for
* switching a switch 'on' and 'off'.
"""

from .device import Device  # Import the base Device class
from .remote_value_switch import RemoteValueSwitch  # Import the RemoteValueSwitch class

class Switch(Device):
    """Class for managing a Switch device in the Teletask system."""

    def __init__(self,
                 teletask,
                 name,
                 group_address_switch=None,
                 group_address_switch_state=None,
                 device_updated_cb=None,
                 doip_component="relay"):
        """Initialize the Switch class.

        Args:
            teletask: The Teletask system instance managing the communication.
            name (str): The name of the switch device.
            group_address_switch (str, optional): The group address where the switch command is sent.
            group_address_switch_state (str, optional): The group address for querying the switch state.
            device_updated_cb (function, optional): Callback for when the device state is updated.
            doip_component (str, optional): The Teletask component type (default: 'relay').
        """
        # Call the parent Device class constructor
        super(Switch, self).__init__(teletask, name, device_updated_cb)

        self.doip_component = str(doip_component).upper()  # Ensure component type is uppercase
        self.teletask = teletask  # Reference to the Teletask system
        self.Switch_state = False  # Internal state of the switch

        # Initialize RemoteValueSwitch to handle communication with Teletask bus
        self.switch = RemoteValueSwitch(
            teletask,
            group_address=group_address_switch,
            device_name=self.name,
            after_update_cb=self.after_update,  # Callback after updates
            doip_component=self.doip_component)

        # Register the device with the Teletask system
        self.teletask.register_device(self)

    def __str__(self):
        """Return the Switch object as a readable string."""
        return '<Switch name="{0}" switch="{1}" />'.format(self.name, self.switch.group_address)

    @property
    def state(self):
        """Return the current switch state of the device (True for ON, False for OFF)."""
        return self.switch.value == RemoteValueSwitch.Value.ON

    async def set_on(self):
        """Turn the switch ON."""
        await self.switch.on()

    async def set_off(self):
        """Turn the switch OFF."""
        await self.switch.off()

    async def change_state(self, value):
        """Change the state of the switch.

        Args:
            value: The desired state (ON/OFF).
        """
        await self.switch.state(value)

    async def current_state(self):
        """Fetch and return the current state of the switch."""
        await self.switch.current_state()

    async def do(self, action):
        """Execute actions on the switch.

        Args:
            action (str): The action to perform ("on" or "off").
        """
        if action == "on":
            await self.set_on()  # Turn the switch on
        elif action == "off":
            await self.set_off()  # Turn the switch off
        else:
            self.teletask.logger.debug("Could not understand action %s for device %s", action, self.get_name())

    def has_group_address(self, var):
        """Check if the device has a specific group address (returns False for Switch)."""
        return False

    def __eq__(self, other):
        """Equality check for Switch objects (compares internal states)."""
        return self.__dict__ == other.__dict__
