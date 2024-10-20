"""
Client is an abstraction for handling the complete UDP io.
The module is build upon asyncio udp functions.
Due to lame support of UDP multicast within asyncio some special treatment for multicast is necessary.
"""
import asyncio
import socket
import binascii
import time

#from teletask.exceptions import CouldNotParseTeletaskIP, XTeletaskException
from teletask.doip import Frame, FrameQueue


class Client:
    """Class for handling (sending and receiving) TCP packets."""

    # pylint: disable=too-few-public-methods

    class Callback:
        """Callback class for handling callbacks for different 'service types' of received packets."""

        def __init__(self, callback, service_types=None):
            """Initialize Callback class.
            
            Args:
                callback: The function to call when a packet of the specified service type is received.
                service_types: A list of service types that this callback should listen for.
            """
            self.callback = callback
            self.service_types = service_types or []  # Initialize with an empty list if None provided.


        def has_service(self, service_type):
            """Test if callback is listening for the given service type.
            
            Args:
                service_type: The type of service to check against.
            
            Returns:
                bool: True if the callback is listening for the service type, False otherwise.
            """
            return len(self.service_types) == 0 or service_type in self.service_types

    class ClientFactory(asyncio.Protocol):
        """Abstraction for managing the asyncio-tcp transports."""

        def __init__(self, host, port, data_received_callback=None, teletask=None):
            """Initialize ClientFactory class.
            
            Args:
                host: The host address for the TCP connection.
                port: The port for the TCP connection.
                data_received_callback: Callback to call when data is received.
                teletask: Reference to the Teletask instance for logging and other functionalities.
            """
            self.host = host
            self.port = port
            self.data_received_callback = data_received_callback  # Callback for received data.
            self.teletask = teletask  # Reference to the Teletask instance.

        def connection_made(self, transport):
            """Assign transport. Callback after TCP connection is made.
            
            Args:
                transport: The transport object representing the TCP connection.
            """
            self.transport = transport  # Save the transport object for later use.

        def data_received(self, data):
            """Call assigned callback. Callback for datagram received.
            
            Args:
                data: The data received over the TCP connection.
            """
            if self.data_received_callback is not None:
                self.data_received_callback(data)  # Call the callback with the received data.

        def error_received(self, exc):
            """Handle errors. Callback for error received.
            
            Args:
                exc: The exception that occurred.
            """
            if hasattr(self, 'teletask'):
                self.teletask.logger.warning('Error received: %s', exc)  # Log the error.

        def connection_lost(self, exc):
            """Log error. Callback for connection lost.
            
            Args:
                exc: The exception or error associated with the lost connection.
            """
            if hasattr(self, 'teletask'):
                self.teletask.logger.info('Closing transport %s', exc)  # Log the closure of the transport.
        
        
        def send(self, msg):
            """Send a message over the TCP connection.
            
            Args:
                msg: The message to send.
            """
            self.transport.write(msg)  # Write the message to the transport.

    def __init__(self, teletask, host, port, telegram_received_callback=None):
        """Initialize Client class.
        
        Args:
            teletask: Reference to the Teletask instance for logging and processing.
            host: The host address for the TCP connection.
            port: The port for the TCP connection.
            telegram_received_callback: Optional callback for received telegrams.
        """
        self.teletask = teletask  # Reference to the Teletask instance.
        self.host = host  # Host address for the TCP connection.
        self.port = port  # Port for the TCP connection.
        self.callbacks = []  # List to store registered callbacks for received packets.


    def data_received_callback(self, raw):
        """Parse and process Teletask frame. Callback for having received a TCP packet.
        
        Args:
            raw: The raw data received over the TCP connection.
        """
        if raw:
            try:
                frame_queue = FrameQueue()  # Create a FrameQueue instance to handle frames.
                frames = frame_queue.process_frames(raw)  # Process raw data into frames.
                for frame in frames:
                    self.teletask.logger.info("Received: %s", frame)  # Log the received frame.
                    self.handle_teletaskframe(frame)  # Handle the received frame.

            except Exception as ex:
                self.teletask.logger.exception(ex)  # Log any exception that occurs.

    def handle_teletaskframe(self, frame):
        """Handle Frame and call all callbacks that watch for the service type identifier.
        
        Args:
            frame: The Teletask frame to handle.
        """
        handled = False
        for callback in self.callbacks:
            callback.callback(frame, self)  # Call the callback with the frame and the client instance.
            handled = True  # Mark that a callback was handled.

        if not handled:
            self.teletask.logger.debug("UNHANDLED: %s", frame)  # Log if no callback handled the frame.

    def register_callback(self, callback):
        """Register a callback for handling received packets.
        
        Args:
            callback: The function to be called for received packets.
        
        Returns:
            Client.Callback: The registered callback object.
        """
        callb = Client.Callback(callback)  # Create a new Callback instance.
        self.callbacks.append(callb)  # Add it to the list of callbacks.
        return callb

    def unregister_callback(self, callb):
        """Unregister a previously registered callback.
        
        Args:
            callb: The Callback instance to unregister.
        """
        self.callbacks.remove(callb)  # Remove the callback from the list.

    async def connect(self):
        """Connect to the TCP socket. Open UDP port and build multicast socket if necessary."""
        client_factory = Client.ClientFactory(
            host=self.host, 
            port=self.port, 
            data_received_callback=self.data_received_callback, 
            teletask=self.teletask
        )
        
        # old code: (reader, writer) = await self.teletask.loop.create_connection(

        # Connect using asyncio create_connection for protocols
        transport, protocol = await self.teletask.loop.create_connection(
            lambda: client_factory,
            host=self.host,
            port=self.port
        )

        # old code: self.reader = reader  # Save the reader object.
        # old code: self.writer = writer  # Save the writer object.
        self.writer = protocol  # Set writer (which contains transport)
        self.reader = transport  # Set reader (the transport itself)
        

    async def send_telegram(self, frame):
        """Send a telegram frame.
        
        Args:
            frame: The telegram frame to send.
        """
        self.send(frame)  # Send the frame using the send method.

    def send(self, frame):
        """Send Frame to socket.
        
        Args:
            frame: The frame to send.
        """
        self.teletask.logger.info("Sending: %s", frame)  # Log the frame being sent.
        self.writer.send(frame.to_teletask().encode())  # Encode the frame and send it.
        #time.sleep(0.2)

    async def stop(self):
        """Stop the TCP socket."""
        # old code: self.reader.close()  # Close the reader socket.
        # old code: self.writer.close()  # Close the writer socket.
        
        # Close the transport if available
        if self.writer and hasattr(self.writer, 'transport'):
            self.writer.transport.close()  # Correct way to close the transport

        if self.reader:
            self.reader.close()  # Close the reader socket, if it's defined
        