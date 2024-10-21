"""
Module for DoIP Responses.

This module processes and interprets Teletask DoIP (Digital over IP) response
frames. It includes a `FrameQueue` class to manage and process incoming raw data,
and a `Frame` class that represents the processed frame structure.

Classes:
    - FrameQueue: Manages the processing of incoming raw DoIP response packets.
    - Frame: Represents a processed DoIP frame with its various components.

Functions:
    - process_frames: Processes a batch of raw data and extracts relevant frames.
    - process_frame: Handles individual frame processing and returns a `Frame` object.
"""

import re
from teletask.doip import Telegram, TelegramFunction, TelegramCommand


class FrameQueue:
    """Class responsible for processing DoIP frames.

    This class receives raw data (likely from a Teletask system), splits it into
    identifiable packets, processes those packets, and returns processed frames.
    """

    def __init__(self):
        """Initialize the FrameQueue object.

        This constructor sets up the queue, although no specific attributes are 
        initialized here.
        """
        pass

    def process_frames(self, raw):
        """Process a batch of raw data and extract individual frames.

        Args:
            raw (list): A list of raw integers representing the incoming data.

        Returns:
            list: A list of `Frame` objects extracted from the raw data.
        """
        # Convert the raw data list into a comma-separated string
        full_packet = ','.join(str(x) for x in raw)
        
        # Use a regex to find packets of interest. The pattern here looks for 
        # specific sequences of 9 elements starting with "2,9,16," followed by any 7 more.
        r1 = re.findall(r"(2,9,16,([0-9]*,?){7})", full_packet)

        result = []
        
        # Loop over each packet found by the regex
        for packet in r1:
            # Process the packet and convert it into a Frame object
            frame = self.process_frame(packet[0])
            
            # Only append if the frame is valid (i.e., not None)
            if frame is not None:
                result.append(frame)

        # Return the list of processed frames
        return result

    def process_frame(self, packet):
        """Process an individual packet string into a Frame object.

        Args:
            packet (str): A string representing a DoIP packet.

        Returns:
            Frame or None: A `Frame` object if processing is successful, or None if there is an error.
        """
        # Split the packet string into a list of individual elements
        event = packet.split(",")

        try:
            if len(event) > 0:
                # Create a payload list from the packet
                payload = [x for x in event]

                # Process key components from the event to create a Frame object
                frame = Frame(
                    payload=payload,
                    doip_component=int(event[4]),  # Component (function)
                    group_address=int(event[6]),   # Group address
                    state=int(event[8])            # State of the component
                )
                return frame

        except Exception as e:
            # Print any exceptions that occur during processing
            print(e)

        return None


class Frame:
    """Class representing an individual DoIP response frame.

    This class contains attributes that describe a single frame from a DoIP system.

    Attributes:
        command (TelegramCommand): The command used in the DoIP frame.
        function (TelegramFunction): The functional unit targeted by the frame.
        group_address (int): The address of the group involved in the command.
        payload (list): The raw data payload of the frame.
        state (int): The current state of the device or function in the frame.
        doip_component (int): The DoIP component involved (such as a relay or dimmer).
        event (any): Additional event information for advanced use cases.
    """

    def __init__(self, command=None, function=None, group_address=None, payload=None, state=None, doip_component=None):
        """Initialize the Frame object.

        Args:
            command (TelegramCommand, optional): The command type of the frame.
            function (TelegramFunction, optional): The function involved in the frame.
            group_address (int, optional): The group address related to the frame.
            payload (list, optional): The raw payload data of the frame.
            state (int, optional): The state of the component (e.g., ON/OFF).
            doip_component (int, optional): The specific DoIP component involved.
        """
        self.command = command
        self.function = function
        self.group_address = group_address
        self.payload = payload
        self.state = state
        self.doip_component = doip_component
        self.event = None  # Optional field for additional event data

    def __str__(self):
        """Return a readable string representation of the Frame object.

        This method formats the frame's key attributes into a human-readable form.
        """
        return '<{0} {1} {2} {3}/>'.format(
            self.doip_component, 
            self.group_address, 
            self.payload, 
            self.state
        )
