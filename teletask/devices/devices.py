"""
Module for handling a vector/array of devices.
This class acts as a container for multiple devices, 
providing functionality to search and manage them.
"""
from .device import Device


class Devices:
    """Class for handling a vector/array of devices."""

    def __init__(self):
        """Initialize Devices class."""
        self.__devices = []  # Internal list to hold device instances
        self.device_updated_cbs = []  # List of callbacks for device updates

    def register_device_updated_cb(self, device_updated_cb):
        """Register a callback for devices being updated."""
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(self, device_updated_cb):
        """Unregister a callback for devices being updated."""
        self.device_updated_cbs.remove(device_updated_cb)

    def __iter__(self):
        """Iterator to allow iteration over devices."""
        yield from self.__devices

    def devices_by_group_address(self, group_address):
        """Return device(s) that match the specified group address."""
        for device in self.__devices:
            if device.has_group_address(group_address):
                yield device  # Yielding devices that match the group address

    def __getitem__(self, key):
        """Return device by name or by index."""
        for device in self.__devices:
            if device.name == key:
                return device  # Return device matching the name
        if isinstance(key, int):
            return self.__devices[key]  # Return device by index
        raise KeyError(f"Device not found: {key}")  # Raise KeyError if not found

    def __len__(self):
        """Return the number of devices within the vector."""
        return len(self.__devices)

    def __contains__(self, key):
        """Check if a device with the specified name exists."""
        for device in self.__devices:
            if device.name == key:
                return True  # Return True if the device exists
        return False  # Return False if not found

    def add(self, device):
        """Add a device to the devices vector."""
        if not isinstance(device, Device):
            raise TypeError("Only instances of Device can be added.")
        device.register_device_updated_cb(self.device_updated)  # Register update callback
        self.__devices.append(device)  # Append device to internal list

    async def device_updated(self, device):
        """Call all registered device updated callbacks for the specified device."""
        for device_updated_cb in self.device_updated_cbs:
            await device_updated_cb(device)  # Await each callback

    async def sync(self):
        """Read the state of devices from the Teletask bus."""
        for device in self.__devices:
            await device.sync()  # Sync each device with the Teletask bus
