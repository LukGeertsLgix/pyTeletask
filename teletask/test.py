"""Example for switching a light on and off."""
import asyncio  # For handling asynchronous operations
import random   # To generate random brightness levels
import logging  # To configure logging
from teletask import Teletask  # Import the Teletask protocol handler in client.py
from teletask.devices import Light  # Import the Light class for controlling lights
from teletask.devices import Dimmer  # Import the Dimmer class for controlling dimmable lights

class HomeRelays:
    """List of my relays."""
    OverloopWand = '1'
    OverloopBureau = '14'
    MasterPlafond = '2'
    MasterWand = '19'
    EetkamerPlafond = '3'
    KeukenOntbijt = '4'
    KeukenAanrecht = '9'
    VoordeurSpots = '5'
    VoordeurWand = '8'
    WC = '6'
    SalonWand = '7'
    SalonSpots = '10'
    ZijdeurWand = '11'
    ZijdeurPlafond = '20'
    KelderPlafond = '12'
    BadkamerDouche = '13'
    BadkamerSpiegel = '24'
    SlaapkamerRechtsWand = '15'
    SlaapkamerRechtsPlafond = '17'
    SlaapkamerLinksPlafond = '16'
    SlaapkamerLinksWand = '18'
    Oprit = '21'
    TuinPin = '22'
    TuinGrondspot = '23'
    ZwembadLicht = '25'
    ZwembadRolOpen = '26'
    ZwembadRolToe = '28'

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
    lightObject = Light(doip,
                  name='SalonSpots',  # Name of the light
                  group_address_switch=HomeRelays.OverloopBureau,  # Address used for switching the light
                  doip_component="relay")  # This light uses a relay to switch on/off
    
    # Turn the light on, wait for 2 seconds then turn it off and wait for 2 seconds
    print(f"Turning {lightObject.name} ON")
    await lightObject.set_on()  # Turn on
    await asyncio.sleep(2)
    print(f"Turning {lightObject.name} OFF")
    await lightObject.set_off()  # Turn off
    await asyncio.sleep(2)

    """
    # Light 2: A dimmable light with a separate relay to turn on/off and control brightness
    light2 = Light(doip,
                name='Stalamp2',  # Name of the light
                group_address_switch='32',  # Address for switching on/off
                group_address_brightness='1',  # Address for controlling brightness
                doip_component="relay")  # This light also uses a relay
    
    # Turn the light on, randomly set brightness, and turn it off
    print("Turning light2 ON")
    await light2.set_on()  # Turn light2 on
    await asyncio.sleep(1)
    brightness2 = int(random.uniform(0, 100))  # Random brightness value between 0 and 100%
    print(f"Setting light2 brightness to {brightness2}%")
    await light2.set_brightness(brightness2)  # Set brightness
    await asyncio.sleep(1)
    print("Turning light2 OFF")
    await light2.set_off()  # Turn light2 off
    await asyncio.sleep(1)
    """

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