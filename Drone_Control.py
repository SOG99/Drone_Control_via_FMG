import logging
import sys
import time
import threading
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

# Add the path to the directory where cflib is installed.
sys.path.append('/C:/Users/User/AppData/Local/Programs/Python/Python311/Lib/site-packages')

# URI of the Crazyflie drone
URI = 'radio://0/80/2M/E7E7'
# Default height for take-off
DEFAULT_HEIGHT = 0.5

# Event object for signaling deck attachment
deck_attached_event = Event()

# Event object for emergency shutdown
emergency_event = Event()

# Event object for forward motion
forward_event = Event()

# Event object for backward motion
backward_event = Event()

# Event object for left motion
left_event = Event()

# Event object for right motion
right_event = Event()

# Configure logging level to ERROR
logging.basicConfig(level=logging.ERROR)

# Function for  take-off and move sequence
def take_off_and_hover(scf):
    # Context manager for MotionCommander
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        # Stay hovering until emergency shutdown event is set
        while not emergency_event.is_set():
            if forward_event.is_set():
                mc.forward(0.3)
                forward_event.clear()  # Reset the event after executing forward motion
                time.sleep(0.3)
            elif backward_event.is_set():
                mc.forward(-0.3)  # Move backward using negative velocity
                backward_event.clear()  # Reset the event after executing backward motion
                time.sleep(0.3)
            elif left_event.is_set():
                mc.left(0.3)
                left_event.clear()  # Reset the event after executing left motion
            elif right_event.is_set():
                mc.right(0.3)
                right_event.clear()  # Reset the event after executing right motion
            time.sleep(0.1)

# Callback function for parameter updates related to deck attachment
def param_deck_flow(_, value_str):
    # Convert parameter value to integer
    value = int(value_str)
    # Print the value (for debugging purposes)
    print(value)
    # If value is non-zero, set the deck_attached_event
    if value:
        deck_attached_event.set()
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')

# Function for handling user input to trigger emergency shutdown, movement, etc.
def user_input_handler():
    while True:
        user_input = input("Press 'Enter' to initiate emergency shutdown, '1' to move forward, '2' to move backward, '3' to move left, or '4' to move right: ")
        if user_input == '':
            emergency_event.set()
            break
        elif user_input == '1':
            forward_event.set()
        elif user_input == '2':
            backward_event.set()
        elif user_input == '3':
            left_event.set()
        elif user_input == '4':
            right_event.set()

# Main execution
if __name__ == '__main__':
    # Initialize Crazyflie drivers
    cflib.crtp.init_drivers()

    # Connect to the Crazyflie
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        # Register param_deck_flow as a callback for parameter updates
        scf.cf.param.add_update_callback(group='deck', name='bcFlow2', cb=param_deck_flow)
        # Wait for 1 second
        time.sleep(1)

        # If deck attachment event is not set within 5 seconds, print error message and exit
        if not deck_attached_event.wait(timeout=5):
            print('No flow deck detected!')
            sys.exit(1)

        # Start the user input thread
        input_thread = threading.Thread(target=user_input_handler)
        input_thread.start()

        # Execute the take-off and hover sequence
        take_off_and_hover(scf)

        # Wait for the user input thread to finish
        #input_thread.join()
