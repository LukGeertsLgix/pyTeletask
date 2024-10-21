"""
Module for queuing telegrams.
When a device wants to send a telegram to the Teletask bus, it must queue it to the TelegramQueue within XTeletask.
The underlying TeletaskIPInterface polls the queue and sends the packets to the correct Teletask/IP abstraction (Tunneling or Routing).
You may register callbacks to be notified when a telegram is pushed to the queue.
"""

import asyncio
from teletask.doip import Telegram, TelegramFunction, TelegramHeartbeat
from teletask.exceptions import TeletaskException


class TelegramQueue:
    """Class for managing a telegram queue."""

    class Callback:
        """Callback class for handling telegram received callbacks."""
        
        def __init__(self, callback):
            """Initialize Callback class."""
            self.callback = callback

    def __init__(self, teletask):
        """Initialize TelegramQueue class."""
        self.teletask = teletask
        self.telegram_received_cbs = []  # List of callbacks for received telegrams
        self.queue_stopped = asyncio.Event()  # Event to signal stopping the queue

    def register_telegram_received_cb(self, telegram_received_cb):
        """Register a callback for telegrams received from the Teletask bus."""
        callback = TelegramQueue.Callback(telegram_received_cb)
        self.telegram_received_cbs.append(callback)  # Store the callback
        return callback

    def unregister_telegram_received_cb(self, telegram_received_cb):
        """Unregister a callback for telegrams received from the Teletask bus."""
        self.telegram_received_cbs.remove(telegram_received_cb)  # Remove the callback

    async def start(self):
        """Start the telegram queue."""
        self.teletask.loop.create_task(self.run())  # Run the telegram processing loop
        asyncio.ensure_future(self.start_heartbeat())  # Start heartbeat task

    async def start_heartbeat(self):
        """Send periodic heartbeat telegrams."""
        while True:
            telegram = TelegramHeartbeat()  # Create a heartbeat telegram
            await self.teletask.telegrams.put(telegram)  # Queue the heartbeat telegram
            await asyncio.sleep(10)  # Wait for 10 seconds before sending the next heartbeat

    async def run(self):
        """Endless loop for processing telegrams."""
        while True:
            telegram = await self.teletask.telegrams.get()  # Wait for a telegram from the queue

            # Break the loop if None is pushed to the queue
            if telegram is None:
                break

            await self.process_telegram(telegram)  # Process the retrieved telegram
            self.teletask.telegrams.task_done()  # Mark the telegram as processed

        self.queue_stopped.set()  # Signal that the queue has stopped

    async def stop(self):
        """Stop the telegram queue."""
        self.teletask.logger.debug("Stopping TelegramQueue")
        await self.teletask.telegrams.put(None)  # Push None to stop the queue
        await self.queue_stopped.wait()  # Wait until the queue has stopped

    async def process_all_telegrams(self):
        """Process all telegrams currently in the queue."""
        while not self.teletask.telegrams.empty():
            telegram = self.teletask.telegrams.get_nowait()  # Get telegram without waiting
            await self.process_telegram(telegram)  # Process the telegram
            self.teletask.telegrams.task_done()  # Mark it as done

    async def process_telegram(self, telegram):
        """Process an incoming or outgoing telegram."""
        try:
            if isinstance(telegram, Telegram):  # Check if it's a telegram instance
                await self.process_telegram_incoming(telegram)  # Process as incoming
            else:
                await self.process_telegram_outgoing(telegram)  # Process as outgoing
        except Exception as ex:
            self.teletask.logger.error("Error while processing telegram: %s", ex)

    async def process_telegram_outgoing(self, telegram):
        """Process an outgoing telegram."""
        if self.teletask.teletaskip_interface is not None:
            await self.teletask.teletaskip_interface.send_telegram(telegram)  # Send telegram
        else:
            self.teletask.logger.warning("No TeletaskIP interface defined")

    async def process_telegram_incoming(self, telegram):
        """Process an incoming telegram."""
        processed = False  # Flag to check if the telegram has been processed
        for telegram_received_cb in self.telegram_received_cbs:
            if telegram.doip_component is not None:
                # Update the component state based on the telegram
                await self.update_component_state(telegram.doip_component, telegram.group_address, telegram.state)
                ret = await telegram_received_cb.callback(telegram)  # Call the registered callback
                if ret:
                    processed = True  # Mark as processed

    async def update_component_state(self, doip_component, group_address, state):
        """Update the state of the specified component."""
        doip_component_name = TelegramFunction(doip_component).name  # Get the component name

        if doip_component_name != 'None' and group_address is not None:
            if doip_component_name in self.teletask.registered_devices:
                try:
                    remote = self.teletask.registered_devices[doip_component_name][str(group_address)]
                    await remote.change_state(state)  # Update the remote state
                except KeyError:
                    self.teletask.logger.debug("Received an update from an unknown or unregistered component.")
                    self.teletask.logger.debug("Name: %s, Address: %s, State: %s", doip_component_name, str(group_address), state)
