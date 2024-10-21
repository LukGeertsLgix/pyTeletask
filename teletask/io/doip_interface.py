"""
TeletaskDoIPInterface manages Teletask/DoIP connections.
* It searches for available devices and connects with the corresponding connect method.
* It passes Teletask telegrams from the network and
* provides callbacks after having received a telegram from the network.
"""
from enum import Enum
from platform import system as get_os_name

from .client import Client

from teletask.exceptions import TeletaskException

class TeletaskDoIPInterface():
    """Class for managing Teletask/DoIP Tunneling or Routing connections."""

    def __init__(self, teletask):
        """Initialize TeletaskDoIPInterface class.
        
        Args:
            teletask: An instance of the Teletask class that provides 
                       context and functionality for managing connections.
        """
        self.teletask = teletask  # Store reference to the Teletask instance

    async def start(self, host, port, auto_reconnect, auto_reconnect_wait):
        """Start Teletask/DoIP.
        
        Connect to the specified host and port using the Client class.
        
        Args:
            host: The hostname or IP address of the Teletask device.
            port: The port number to connect to.
            auto_reconnect: Flag to enable automatic reconnection.
            auto_reconnect_wait: Time to wait before attempting reconnection.
        """
        self.teletask.logger.debug("Create an instance of the Client for managing connections")
        # Create an instance of the Client for managing connections
        self.interface = Client(self.teletask, host, port, telegram_received_callback=self.telegram_received)
        
        # Register a callback to handle responses received from the Client
        self.teletask.logger.debug("Register a callback to handle responses received from the Client")
        self.interface.register_callback(self.response_rec_callback)

        # Establish connection to the Teletask device
        self.teletask.logger.debug("Trying to connect to %s:%s ", host, port)
        await self.interface.connect()

    def response_rec_callback(self, frame, _):
        """Verify and handle DoIP frame. Callback from internal client.
        
        Args:
            frame: The received frame that needs to be processed.
            _: Unused parameter, typically representing the client instance.
        """
        self.telegram_received(frame)  # Process the received telegram

    async def stop(self):
        """Stop connected interface.
        
        Close the connection and clean up resources.
        """
        if self.interface is not None:
            await self.interface.stop()  # Stop the client connection
            self.interface = None  # Clear the interface reference

    def telegram_received(self, telegram):
        """Put received telegram into queue. Callback for having received telegram.
        
        This method adds the received telegram to the event loop queue for further processing.
        
        Args:
            telegram: The telegram received from the network.
        """
        self.teletask.loop.create_task(self.teletask.telegrams.put(telegram))

    async def send_telegram(self, telegram):
        """Send telegram to connected device.
        
        This method sends a telegram to the connected Teletask device using the client interface.
        
        Args:
            telegram: The telegram to be sent.
        """
        await self.interface.send_telegram(telegram)  # Use the client to send the telegram