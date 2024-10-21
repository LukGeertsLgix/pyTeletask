"""
Device is the base class for all implemented devices (e.g., Lights, Switches, Sensors).
It provides basic functionality for reading the state from the Teletask bus and
sending commands to control devices.

Classes:
    - Device: Base class representing a device connected to the Teletask bus.

Methods:
    - register_device_updated_cb: Register a callback to be invoked when the device state updates.
    - unregister_device_updated_cb: Unregister a previously registered callback.
    - sync: Sync the device state by reading from the Teletask bus.
    - send: Send a telegram (message) to update the device state.
    - process: Handle incoming telegrams (messages) from the Teletask bus.
"""

from teletask.exceptions import TeletaskException
from teletask.doip import Telegram  # , TelegramType (commented out but probably used elsewhere)


class Device:
    """Base class for Teletask devices.

    This class serves as the foundation for all devices that interact with
    the Teletask home automation system. It handles basic operations like
    state synchronization and processing commands from the Teletask bus.

    Attributes:
        teletask: The Teletask system instance managing the communication.
        name (str): The name of the device.
        device_updated_cbs (list): List of callback functions to notify on device state updates.
    """

    def __init__(self, teletask, name, device_updated_cb=None):
        """Initialize the Device class.

        Args:
            teletask: The Teletask instance managing communication.
            name (str): The name of the device.
            device_updated_cb (function, optional): A callback function invoked when the device is updated.
        """
        self.teletask = teletask  # The Teletask system instance that controls communication.
        self.doip_component = "UNKNOWN"  # Component type, not defined here; could be overridden in subclasses.
        self.name = name  # Device name.
        self.device_updated_cbs = []  # List of callback functions for device updates.
        
        # Register the callback if provided.
        if device_updated_cb is not None:
            self.register_device_updated_cb(device_updated_cb)

    def register_device_updated_cb(self, device_updated_cb):
        """Register a callback to be invoked when the device state is updated.

        Args:
            device_updated_cb (function): The callback function to be added.
        """
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(self, device_updated_cb):
        """Unregister a callback that was previously registered.

        Args:
            device_updated_cb (function): The callback function to be removed.
        """
        self.device_updated_cbs.remove(device_updated_cb)

    async def after_update(self):
        """Execute registered callbacks after the internal state has been changed.

        This method is called after the device's state has been updated, allowing
        registered callbacks to react to the change.
        """
        for device_updated_cb in self.device_updated_cbs:
            await device_updated_cb(self)

    async def sync(self, wait_for_result=True):
        """Synchronize the state of the device from the Teletask bus.

        This method reads the device's current state by querying the Teletask bus.

        Args:
            wait_for_result (bool, optional): Whether to wait for the result or not (default is True).
        """
        try:
            await self._sync_impl(wait_for_result)
        except TeletaskException as ex:
            self.teletask.logger.error("Error while syncing device: %s", ex)

    async def _sync_impl(self, wait_for_result=True):
        """Internal implementation for syncing device state.

        Args:
            wait_for_result (bool, optional): Whether to wait for the result (default is True).
        """
        self.teletask.logger.debug("Sync %s", self.name)  # Log syncing operation.

        # Loop over group addresses to request the state of the device.
        for group_address in self.state_addresses():
            from teletask.core import ValueReader
            value_reader = ValueReader(self.teletask, group_address)

            if wait_for_result:
                # Wait for the response telegram after reading.
                telegram = await value_reader.read()
                if telegram is not None:
                    await self.process(telegram)  # Process the incoming telegram.
                else:
                    self.teletask.logger.warning("Could not read value of %s %s", self, group_address)
            else:
                # Send a group read request without waiting for the result.
                await value_reader.send_group_read()

    async def send(self, group_address, payload=None, response=False):
        """Send a telegram (message) to the Teletask bus.

        This method allows sending commands to devices on the Teletask bus.

        Args:
            group_address (int): The group address of the device.
            payload (any, optional): The data to be sent (default is None).
            response (bool, optional): Whether this is a response telegram (default is False).
        """
        telegram = Telegram()  # Create a new Telegram object.
        telegram.group_address = group_address  # Set the group address.
        telegram.payload = payload  # Set the payload data.
        
        # Set the telegram type based on whether it's a response or a regular write command.
        telegram.telegramtype = TelegramType.GROUP_RESPONSE if response else TelegramType.GROUP_WRITE
        await self.teletask.telegrams.put(telegram)  # Send the telegram to the Teletask bus.

    def state_addresses(self):
        """Return the group addresses to be requested for syncing the device state.

        This method is meant to be overridden by subclasses to define the relevant
        addresses for a particular device.

        Returns:
            list: List of group addresses.
        """
        # Default implementation returns an empty list.
        return []

    async def process(self, telegram):
        """Process an incoming telegram.

        This method is responsible for handling messages received from the
        Teletask bus. It should be overridden by subclasses to process
        specific types of telegrams.

        Args:
            telegram (Telegram): The telegram received from the Teletask bus.
        """
        pass  # Can be extended by subclasses for specific device behavior.

    async def process_group_read(self, telegram):
        """Process an incoming GROUP READ telegram.

        By default, devices do not answer to group read requests, but subclasses
        can override this method to provide specific responses.

        Args:
            telegram (Telegram): The telegram received from the Teletask bus.
        """
        pass  # Can be extended by subclasses for specific device behavior.

    async def process_group_response(self, telegram):
        """Process an incoming GROUP RESPONSE telegram.

        By default, this is mapped to the group write process, but subclasses
        can implement custom behavior for group responses.

        Args:
            telegram (Telegram): The telegram received from the Teletask bus.
        """
        await self.process_group_write(telegram)  # Default action is to treat it as a group write.

    async def process_group_write(self, telegram):
        """Process an incoming GROUP WRITE telegram.

        This method handles write telegrams, where devices are commanded to change
        their state. By default, no action is taken, but subclasses can override it
        for specific behavior.

        Args:
            telegram (Telegram): The telegram received from the Teletask bus.
        """
        pass  # Can be extended by subclasses for specific device behavior.

    def get_name(self):
        """Return the name of the device.

        Returns:
            str: The name of the device.
        """
        return self.name

    async def do(self, action):
        """Execute a device-specific action.

        This method is used to perform actions on the device, but it is meant to be
        overridden by subclasses that define specific actions.

        Args:
            action (str): The action to be executed.

        Logs:
            If the action is not implemented, it logs a message indicating that.
        """
        self.teletask.logger.info("Do not implemented action '%s' for %s", action, self.__class__.__name__)
