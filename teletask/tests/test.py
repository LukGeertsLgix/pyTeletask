"""Example for switching a light on and off."""
import asyncio  # For handling asynchronous operations
import random   # To generate random brightness levels
import logging  # To configure logging
from enum import Enum
from teletask import Teletask  # Import the Teletask protocol handler in client.py
from teletask.devices import Light  # Import the Light class for controlling lights
from teletask.devices import Dimmer  # Import the Dimmer class for controlling dimmable lights

class HomeRelays(Enum):
    """Enum class with list of my relays."""
    OVERLOOP_WAND = 1                # 2nd floor - Hall - Lights wall
    OVERLOOP_BUREAU = 14             # 2nd floor - Hall - Light desk
    MASTER_PLAFOND = 2               # 2nd floor - Master Bedroom - Light ceiling
    MASTER_WAND = 19                 # 2nd floor - Master Bedroom - Lights wall
    EETKAMER_PLAFOND = 3             # Groundfloor - Dining area - Lights Ceiling
    KEUKEN_ONTBIJT = 4               # Groundfloor - Kitchen area - Lights Breakfast Table
    KEUKEN_AANRECHT = 9              # Groundfloor - Kitchen area - Lights Sink
    VOORDEUR_SPOTS = 5               # Groundfloor - Front door - Lights ceiling
    VOORDEUR_WAND = 8                # Groundfloor - Front door - Light Wall
    WC = 6                           # Groundfloor - Toilet - Light
    SALON_WAND = 7                   # Groundfloor - Living area - Light Wall
    SALON_SPOTS = 10                 # Groundfloor - Living area - Lights ceiling
    ZIJDEUR_WAND = 11                # Groundfloor - Side door - Lights Wall
    ZIJDEUR_PLAFOND = 20             # Groundfloor - Side door - Lights Ceiling
    KELDER_PLAFOND = 12              # Basement - Basement - Lights Ceiling
    BADKAMER_DOUCHE = 13             # 2nd floor - Bathroom - Lights Shower
    BADKAMER_SPIEGEL = 24            # 2nd floor - Bathroom - Light Mirror
    SLAAPKAMER_RECHTS_WAND = 15      # 2nd floor - Right Bedroom - Lights wall
    SLAAPKAMER_RECHTS_PLAFOND = 17   # 2nd floor - Right Bedroom - Lights Ceiling
    SLAAPKAMER_LINKS_PLAFOND = 16    # 2nd floor - Left Bedroom - Lights wall
    SLAAPKAMER_LINKS_WAND = 18       # 2nd floor - Left Bedroom - Lights Ceiling
    OPRIT = 21                       # Outside - Driveway - Lights
    TUIN_PIN = 22                    # Outside - Garden - Pin Lights
    TUIN_GROUND = 23                 # Outside - Garden - Ground Lights
    ZWEMBAD_LICHT = 25               # Outside - Swimming Pool - Lights
    ZWEMBAD_ROL_OPEN = 26            # Outside - Swimming Pool - Open Shutter
    ZWEMBAD_ROL_TOE = 28             # Outside - Swimming Pool - Close Shutter

async def main(ip_address, port):
    """Connect to KNX/IP bus, switch on light, wait 2 seconds and switch it off again."""
    
    # Configure logging if it hasn't been configured yet
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.DEBUG,  # Set minimum log level to DEBUG
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Custom log format
            filename='test.py.log',  # Log output to a file
            filemode='w'  # Overwrite the log file on each run
        )

    # Create a Teletask instance and connect to the Teletask system over IP
    print(f"Connecting to Teletask system at {ip_address}:{port}")
    doip = Teletask()
    await doip.start(ip_address, port)  # Connect using variables for IP and port
    
    # Light 1: A simple light without a dimmer, controlled via a relay
    lightObject1 = Light(doip,
                  name='OverloopBureau',  # Name of the light
                  group_address_switch=HomeRelays.OVERLOOP_BUREAU,  # Address used for switching the light
                  doip_component="relay")  # This light uses a relay to switch on/off
    
    # Turn the light on, wait for 2 seconds then turn it off and wait for 2 seconds
    print(f"Getting current state from {lightObject1.name} ")
    await lightObject1.current_state()  # Get current state
    await asyncio.sleep(2)
    print(f"Turning {lightObject1.name} ON")
    await lightObject1.set_on()  # Turn on
    await asyncio.sleep(2)
    print(f"Getting current state from {lightObject1.name} ")
    await lightObject1.current_state()  # Get current state
    await asyncio.sleep(2)
    print(f"Turning {lightObject1.name} OFF")
    await lightObject1.set_off()  # Turn off
    await asyncio.sleep(2)

    # Light 2: A dimmable light with a separate relay to turn on/off and control brightness
    lightObject2 = Light(doip,
                name='OverloopWand',  # Name of the light
                group_address_switch=HomeRelays.OVERLOOP_WAND,  # Address for switching on/off
                group_address_brightness='1',  # Address for controlling brightness
                doip_component="relay")  # This light also uses a relay
    
    # Turn the light on, randomly set brightness, and turn it off
    print(f"Turning {lightObject2.name} ON")
    await lightObject2.set_on()  # Turn lightObject2 on
    await asyncio.sleep(1)
    brightness2 = int(random.uniform(0, 100))  # Random brightness value between 0 and 100%
    print(f"Setting {lightObject2.name} brightness to {brightness2}%")
    await lightObject2.set_brightness(brightness2)  # Set brightness
    await asyncio.sleep(1)
    print(f"Turning {lightObject2.name} OFF")
    await lightObject2.set_off()  # Turn lightObject2 off
    await asyncio.sleep(1)

    """
    # Light 3: A dimmable light controlled using the Dimmer class (new in version 1.0.4),
    # without a separate relay, meaning the dimmer itself controls both switching and brightness
    light3 = Dimmer(doip,
                name='Stalamp3',  # Name of the light
                group_address_brightness='5',  # Address for controlling brightness
                doip_component="dimmer")  # This light uses a dimmer for control
    
    # Turn the light on, set a random brightness, then turn it off
    await light3.set_on()  # Turn light3 on
    await asyncio.sleep(5)
    brightness3 = int(random.uniform(0, 100))  # Random brightness value
    print(f"Setting light3 brightness to {brightness3}%")
    await light3.set_brightness(brightness3)  # Set brightness
    await asyncio.sleep(5)
    await light3.set_off()  # Turn light3 off
    await asyncio.sleep(5)
    """
    await asyncio.sleep(5)

    # Disconnect from the Teletask system after all actions are done
    print("Disconnecting from Teletask system")
    await doip.stop()  # Stop the connection to the Teletask system


# pylint: disable=invalid-name

# Define IP and port as variables
ip_address = "192.168.1.22"  # You can change this to any IP address you want to use
port = 55957  # You can change this to any port you want to use

# Get the event loop and run the main function until it completes, passing the IP and port as arguments
loop = asyncio.get_event_loop()
loop.run_until_complete(main(ip_address, port))  # Pass the IP address and port to the main function
loop.close()  # Close the event loop
