"""
Module for managing a remote value in the Teletask system.

A RemoteValue can represent a Teletask-controlled value, which can be either:
- A single group address for both reading and writing,
- Or separate group addresses for reading and writing Teletask values.

This class manages the communication and value conversions needed to control
devices in the Teletask system (e.g., switches, dimmers).
"""
# from teletask.exceptions import CouldNotParseTelegram
from teletask.doip import Telegram, TeletaskConst, TelegramCommand, TelegramFunction, TelegramSetting
import asyncio

class RemoteValue:
    """Base class for managing a remote value in the Teletask system."""

    def __init__(self, teletask, group_address=None, device_name=None, after_update_cb=None, doip_component=None):
        """
        Initialize the RemoteValue class.

        Args:
            teletask: Reference to the main Teletask controller.
            group_address: The Teletask group address associated with this value.
            device_name: Name of the device (default: "Unknown").
            after_update_cb: Callback function to execute after value updates.
            doip_component: The Teletask component type (e.g., "switch", "dimmer").
        """
        self.teletask = teletask  # Main Teletask controller instance
        self.doip_component = doip_component  # Type of Teletask component (e.g., switch, dimmer)
        self.group_address = group_address  # Address on the Teletask bus
        self.brightness_val = 0  # Default brightness value for dimmers
        self.after_update_cb = after_update_cb  # Callback function after updates
        self.device_name = "Unknown" if device_name is None else device_name  # Device name
        self.payload = None  # Holds the current payload (state)

    @property
    def initialized(self):
        """Check if the RemoteValue is initialized with a valid group address."""
        return bool(self.group_address)

    def has_group_address(self, group_address):
        """Check if this remote value has the given group address."""
        return self.group_address == group_address

    def state_addresses(self):
        """Return the group addresses that should be requested to sync the state."""
        if self.group_address:
            return [self.group_address]
        return []

    def payload_valid(self, payload):
        """
        Placeholder to test if the received telegram payload is valid.
        This should be implemented in derived classes to validate specific payloads.

        Args:
            payload: The payload to be validated.

        Returns:
            bool: True if the payload is valid, False otherwise.
        """
        self.teletask.logger.warning("payload_valid not implemented for %s", self.__class__.__name__)
        return True

    def from_teletask(self, payload):
        """
        Placeholder for converting a Teletask payload into a value.
        This should be implemented in derived classes to handle specific conversions.

        Args:
            payload: The raw payload from Teletask.

        Returns:
            Converted value from the payload.
        """
        self.teletask.logger.warning("from_teletask not implemented for %s", self.__class__.__name__)
        return None

    def to_teletask(self, value):
        """
        Placeholder for converting a value into a Teletask payload.
        This should be implemented in derived classes to handle specific conversions.

        Args:
            value: The value to convert into a Teletask-compatible format.

        Returns:
            Payload ready to be sent to Teletask.
        """
        self.teletask.logger.warning("to_teletask not implemented for %s", self.__class__.__name__)
        return None

    async def process(self, telegram):
        """
        Process an incoming telegram from the Teletask bus.
        
        Checks if the telegram's group address matches this device and if the
        payload is valid. If the value has changed, the callback is triggered.

        Args:
            telegram: The received Teletask telegram.

        Returns:
            bool: True if the telegram was successfully processed, False otherwise.
        """
        # Check if the group address matches the one for this remote value
        if not self.has_group_address(telegram.group_address):
            return False
        
        # Validate the payload before processing it
        if not self.payload_valid(telegram.payload):
            raise Exception("Invalid payload received",
                            payload=telegram.payload,
                            group_address=telegram.group_address,
                            device_name=self.device_name)
        
        # If the payload has changed or is being set for the first time, update it
        if self.payload != telegram.payload or self.payload is None:
            self.payload = telegram.payload
            # Trigger the callback if defined
            if self.after_update_cb is not None:
                await self.after_update_cb()

        return True

    @property
    def value(self):
        """
        Get the current value of the remote device.
        
        Returns:
            The converted value based on the stored payload.
        """
        if self.payload is None:
            return None
        return self.from_teletask(self.payload)

    async def current_state(self):
        """
        Send a request to the Teletask bus to get the current state of the device.
        
        Sends a telegram with a GET command to the group address to fetch the current state.
        """
        function = TelegramFunction[self.doip_component]
        telegram = Telegram(command=TelegramCommand.GET, address=int(self.group_address), function=function)
        await self.teletask.telegrams.put(telegram)

    async def send(self, receivedSetting=TelegramSetting.TOGGLE.value, response=False):
        """
        Send a value (payload) to the Teletask bus to control the device.

        Args:
            receivedSetting: The setting to send (e.g., ON/OFF, brightness).
            response: If True, sends a group response. Defaults to False (group write).
        """
        function = TelegramFunction[self.doip_component]

        # Create the value to send based on the device type (dimmer, switch, etc.)
        if self.doip_component == "DIMMER":
            ttvalue = TeletaskValue()
            ttvalue.value = self.brightness_val  # Send brightness level for dimmers
        else:
            ttvalue = TeletaskValue()
            ttvalue.value = receivedSetting  # Send the ON/OFF value for switches
        setting = ttvalue

        # Send the telegram with the setting to the Teletask bus
        telegram = Telegram(command=TelegramCommand.SET, function=function, address=int(self.group_address), setting=setting)
        await self.teletask.telegrams.put(telegram)

    async def set(self, value):
        """
        Set a new value for the device and send it to the Teletask bus.

        Args:
            value: The new value to set for the device.
        """
        if not self.initialized:
            self.teletask.logger.info("Attempting to set value for uninitialized device %s (value: %s)", self.device_name, value)
            return

        # Convert the provided value into a Teletask-compatible payload
        payload = self.to_teletask(value)

        # Update the payload if it's different from the current one
        updated = False
        if self.payload is None or payload != self.payload:
            self.payload = payload
            updated = True

        # Update the brightness value for dimmers
        if value is not None:
            self.brightness_val = value

        # Send the updated value to the bus
        await self.send()

        # Trigger the callback if the value has changed
        if updated and self.after_update_cb is not None:
            await self.after_update_cb()

    async def state(self, raw_value):
        """
        Update the internal state based on a raw value received from Teletask.

        Args:
            raw_value: The raw ON/OFF value received from Teletask.
        """
        value = self.Value.ON if int(raw_value) == TelegramSetting.ON.value else self.Value.OFF

        # Update the internal payload if necessary
        updated = False
        if self.payload is None or self.payload != value:
            self.payload = value
            updated = True

        # Trigger the callback if the value has changed
        if updated and self.after_update_cb is not None:
            await self.after_update_cb()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement (if applicable)."""
        return None

    def group_addr_str(self):
        """Return a string representation of the group address, payload, and value."""
        return '{0}/{1}/{2}/{3}' \
            .format(self.group_address.__repr__(),
                    self.group_address_state.__repr__(),
                    self.payload,
                    self.value)

    def __str__(self):
        """Return the string representation of the RemoteValue object."""
        return '<{} device_name="{}" {}/>'.format(
            self.__class__.__name__,
            self.device_name,
            self.group_addr_str())

    def __eq__(self, other):
        """Check if two RemoteValue objects are equal by comparing their internal states."""
        for key, value in self.__dict__.items():
            if key == "after_update_cb":
                continue
            if key not in other.__dict__:
                return False
            if other.__dict__[key] != value:
                return False
        for key, value in other.__dict__.items():
            if key == "after_update_cb":
                continue
            if key not in self.__dict__:
                return False
        return True

class TeletaskValue:
    """Class representing a value to be sent over the Teletask system."""
    
    def __init__(self):
        self.value = 0  # Default value set to 0 (can represent ON/OFF or brightness)
