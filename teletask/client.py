"""Teletask is an Asynchronous Python module for reading and writing Teletask/DoIP packets."""
import asyncio
import logging
import signal

from sys import platform

import time
from concurrent.futures import ProcessPoolExecutor

from teletask.core import TelegramQueue
from teletask.devices import Devices
from teletask.io import TeletaskDoIPInterface
from teletask.doip import Telegram, TeletaskConst, TelegramCommand, TelegramFunction, TelegramSetting, TelegramHeartbeat

class Teletask:
    """Class for reading and writing Teletask/DoIP packets."""
    DEFAULT_ADDRESS = ''

    def __init__(self, config=None, loop=None, telegram_received_cb=None):
        """Initialize Teletask class.
        
        Args:
            config: Optional configuration for the Teletask module.
            loop: An optional event loop to run asynchronous tasks.
            telegram_received_cb: Optional callback function to handle received telegrams.
        """
        self.devices = Devices()  # Instance to manage connected devices.
        self.telegrams = asyncio.Queue()  # Asynchronous queue for handling telegrams.
        self.loop = loop or asyncio.get_event_loop()  # Use the provided loop or get the current running loop.
        self.sigint_received = asyncio.Event()  # Event to signal when termination is received.
        self.telegram_queue = TelegramQueue(self)  # Queue for processing telegrams.
        self.state_updater = None  # Placeholder for a state updater, if needed.
        self.teletaskip_interface = None  # Placeholder for the Teletask DoIP interface.
        self.started = False  # Flag to indicate if the module is started.
        self.executors = ProcessPoolExecutor(2)  # Executor for handling CPU-bound tasks.
        self.registered_devices = {}  # Dictionary to store registered devices by component type.
        self.logger = logging.getLogger('teletask.log')  # Logger for general logging.
        self.teletask_logger = logging.getLogger('teletask.teletask')  # Logger for Teletask-specific logs.
        self.telegram_logger = logging.getLogger('teletask.telegram')  # Logger for telegram-related logs.

        self.logger.info("Teletask instance created.")

        if telegram_received_cb is not None:
            self.telegram_queue.register_telegram_received_cb(telegram_received_cb)

    def __del__(self):
        """Destructor. Cleaning up if this was not done before."""
        if self.started:
            try:
                task = self.loop.create_task(self.stop())  # Create a task to stop the module.
                self.loop.run_until_complete(task)  # Run until the stop task is complete.
            except RuntimeError as exp:
                self.logger.warning("Could not close loop, reason: %s", exp)  # Log a warning if loop closure fails.

    async def start(self, host=None, port=None, daemon_mode=False):
        """Start Teletask module. Connect to Teletask/DoIP devices and start state updater.
        
        Args:
            host: The host IP address for the Teletask DoIP interface.
            port: The port for the Teletask DoIP interface.
            daemon_mode: If True, run in daemon mode, waiting for termination signal.
        """
        self.teletaskip_interface = TeletaskDoIPInterface(self)  # Initialize the DoIP interface.
        await self.teletaskip_interface.start(host, port, True, 60)  # Start the interface connection.
        await self.telegram_queue.start()  # Start processing telegrams.

        if daemon_mode:
            await self.loop_until_sigint()  # Wait for a SIGINT if in daemon mode.

        self.started = True  # Set the module state to started.

    async def join(self):
        """Wait until all telegrams were processed."""
        await self.telegrams.join()  # Wait for the telegram queue to finish processing.

    async def _stop_teletaskip_interface_if_exists(self):
        """Stop TeletaskIPInterface if initialized."""
        if self.teletaskip_interface is not None:
            await self.teletaskip_interface.stop()  # Stop the interface.
            self.teletaskip_interface = None  # Clear the reference.

    async def stop(self):
        """Stop Teletask module."""
        await self.join()  # Wait for all telegrams to be processed.
        await self.telegram_queue.stop()  # Stop the telegram queue.
        await self._stop_teletaskip_interface_if_exists()  # Stop the DoIP interface.
        self.started = False  # Set the module state to not started.

    async def loop_until_sigint(self):
        """Loop until Ctrl+C was pressed."""
        def sigint_handler():
            """End loop."""
            self.sigint_received.set()  # Set the event to signal termination.

        if platform == "win32":
            self.logger.warning('Windows does not support signals')  # Warn if on Windows.
        else:
            self.loop.add_signal_handler(signal.SIGINT, sigint_handler)  # Add signal handler for Ctrl+C.

        self.logger.warning('Press Ctrl+C to stop')  # Log instruction to the user.
        await self.sigint_received.wait()  # Wait for the termination signal.

    async def register_feedback(self):
        """Register feedback for various device types."""
        # Create and send telegrams for device registration.
        telegram = Telegram(command=TelegramCommand.LOG, function=TelegramFunction.RELAY)
        self.registered_devices["RELAY"] = {}
        await self.telegrams.put(telegram)  # Put telegram in the queue.
        await asyncio.sleep(1)  # Wait for a moment before the next registration.

        telegram = Telegram(command=TelegramCommand.LOG, function=TelegramFunction.DIMMER)
        self.registered_devices["DIMMER"] = {}
        await self.telegrams.put(telegram)
        await asyncio.sleep(1)

        telegram = Telegram(command=TelegramCommand.LOG, function=TelegramFunction.LOCMOOD)
        self.registered_devices["LOCMOOD"] = {}
        await self.telegrams.put(telegram)
        await asyncio.sleep(1)

        telegram = Telegram(command=TelegramCommand.LOG, function=TelegramFunction.GENMOOD)
        self.registered_devices["GENMOOD"] = {}
        await self.telegrams.put(telegram)
        await asyncio.sleep(1)

        telegram = Telegram(command=TelegramCommand.LOG, function=TelegramFunction.FLAG)
        self.registered_devices["FLAG"] = {}
        await self.telegrams.put(telegram)
        await asyncio.sleep(1)


    def register_device(self, device):
        """Register a device to the Teletask module.
        
        Args:
            device: The device object to register.
        """
        if device.doip_component in self.registered_devices:
            # Store the device in the registered_devices dictionary using its group address.
            self.registered_devices[device.doip_component][device.switch.group_address] = device