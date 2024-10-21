"""
Module for managing a light via Teletask.
It provides functionality for:
* Switching a light 'on' and 'off'.
* Adjusting the brightness (if supported).
"""
from .device import Device
from .remote_value_switch import RemoteValueSwitch
from .remote_value_scaling import RemoteValueScaling


class Light(Device):
    """
    Class for managing a light device in the Teletask system.
    
    This class controls the basic lighting features such as switching the light
    on or off, and adjusting its brightness if the light supports dimming.
    """

    def __init__(self,
                 teletask,
                 name,
                 group_address_switch=None,
                 group_address_switch_state=None,
                 group_address_brightness=None,
                 dimmer_address_switch=None,
                 doip_component="relay",
                 device_updated_cb=None):
        """
        Initialize the Light class.

        Args:
            teletask: The main Teletask system object.
            name: The name of the light device.
            group_address_switch: The group address for switching the light on/off.
            group_address_switch_state: The group address for the light's switch state.
            group_address_brightness: The group address for controlling brightness.
            dimmer_address_switch: Address for dimmer controls (optional).
            doip_component: The Teletask component type (default: "relay").
            device_updated_cb: A callback to execute after the device state updates.
        """
        # Initialize the parent Device class
        super(Light, self).__init__(teletask, name, device_updated_cb)

        self.doip_component = str(doip_component).upper()
        self.teletask = teletask
        self.light_state = False  # Default state is off
        
        # Setup switch control for turning the light on/off
        self.switch = RemoteValueSwitch(
            teletask,
            group_address=group_address_switch,
            device_name=self.name,
            after_update_cb=self.after_update,
            doip_component=self.doip_component
        )

        # Setup brightness control (dimming) if supported
        self.brightness = RemoteValueScaling(
            teletask,
            group_address=group_address_brightness,
            device_name=self.name,
            after_update_cb=self.after_update,
            range_from=0,
            range_to=100,
            doip_component="DIMMER"
        )

        # Register the light with the Teletask system
        self.teletask.register_device(self)

    def __str__(self):
        """Return object as a readable string."""
        str_brightness = '' if not self.supports_brightness else \
            ' brightness="{0}"'.format(self.brightness.group_addr_str())

        return '<Light name="{0}" switch="{1}" {2} />'.format(
            self.name, self.switch.group_address, str_brightness)

    @property
    def supports_brightness(self):
        """Check if the light supports brightness control (dimming)."""
        return self.brightness.initialized

    @property
    def state(self):
        """Return the current on/off state of the light."""
        return self.switch.value == RemoteValueSwitch.Value.ON

    async def set_on(self):
        """Turn the light on."""
        await self.switch.on()

    async def set_off(self):
        """Turn the light off."""
        await self.switch.off()

    @property
    def current_brightness(self):
        """Return the current brightness of the light."""
        return self.brightness.value

    async def set_brightness(self, brightness):
        """
        Set the brightness level of the light.

        Args:
            brightness: An integer value (typically 0-100) representing the brightness level.
        """
        if not self.supports_brightness:
            self.teletask.logger.warning("Dimming not supported for device %s", self.get_name())
            return
        await self.brightness.set(brightness)

    async def change_state(self, value):
        """Change the on/off state of the light based on a raw value."""
        await self.switch.state(value)

    async def current_state(self):
        """Request the current state of the light."""
        await self.switch.current_state()

    async def do(self, action):
        """
        Execute commands to control the light.
        
        Args:
            action: The action to perform. Possible values are 'on', 'off', and 'brightness:X' (where X is a brightness level).
        """
        if action == "on":
            await self.set_on()
        elif action == "off":
            await self.set_off()
        elif action.startswith("brightness:"):
            await self.set_brightness(int(action[11:]))
        else:
            self.teletask.logger.debug("Could not understand action %s for device %s", action, self.get_name())

    def has_group_address(self, var):
        """Check if the light has a specific group address (dummy implementation)."""
        return False

    def __eq__(self, other):
        """Compare two light objects for equality."""
        return self.__dict__ == other.__dict__
