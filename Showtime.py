import serial
import numpy as np
import csv
import pickle
from datetime import datetime
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

# Add the path to the directory where cflib is installed
sys.path.append('/C:/Users/User/AppData/Local/Programs/Python/Python311/Lib/site-packages')

# Configure logging level to ERROR
logging.basicConfig(level=logging.ERROR)

# Set up variables for live updating
num_readings = 100
time_stamp = np.zeros(num_readings)
values1 = np.zeros(num_readings)
values2 = np.zeros(num_readings)
values3 = np.zeros(num_readings)
values4 = np.zeros(num_readings)
speed1 = np.zeros(num_readings)
speed2 = np.zeros(num_readings)
speed3 = np.zeros(num_readings)
speed4 = np.zeros(num_readings)
start_time = datetime.now()
frame = 0

# URI of the Crazyflie drone
URI = 'radio://0/80/2M/E7E7'
# Default height for take-off
DEFAULT_HEIGHT = 0.4

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

# Function to update the data 
def predict_frame():
    global time_stamp, values1, values2, values3, values4, speed1, speed2, speed3, speed4
    global frame

    # Record timestamp
    time_stamp[frame] = (datetime.now() - start_time).total_seconds()

    # Receive data from Arduino
    data = ser.readline().decode().strip()

    # Convert received data to numeric format ((values are separated by spaces))
    values = list(map(float, data.split()))

    # Extract individual values
    values1[frame] = values[0]
    values2[frame] = values[1]
    values3[frame] = values[2]
    values4[frame] = values[3]

    # Calculate speed (rate of change)
    if frame > 0:
        speed1[frame] = (values1[frame] - values1[frame - 1]) / (time_stamp[frame] - time_stamp[frame - 1])
        speed2[frame] = (values2[frame] - values2[frame - 1]) / (time_stamp[frame] - time_stamp[frame - 1])
        speed3[frame] = (values3[frame] - values3[frame - 1]) / (time_stamp[frame] - time_stamp[frame - 1])
        speed4[frame] = (values4[frame] - values4[frame - 1]) / (time_stamp[frame] - time_stamp[frame - 1])
    else:
        speed1[frame] = 0
        speed2[frame] = 0
        speed3[frame] = 0
        speed4[frame] = 0
        
    # Make prediction
    X = np.array([[speed1[frame], speed2[frame], speed3[frame], speed4[frame]]])
    prediction = pred.predict(X)
    print(prediction)

    # Stop after num_readings
    if frame + 1 == num_readings:
        ser.close()
    
    frame += 1

    return prediction
    
# Function for  take-off and move sequence
def take_off_and_hover(scf):
    print("Ok Hovering")
    # Context manager for MotionCommander
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        # Stay hovering until emergency shutdown event is set
        while not emergency_event.is_set():
            if forward_event.is_set():
                mc.forward(0.3)
                forward_event.clear()  # Reset the event after executing forward motion
            elif backward_event.is_set():
                mc.forward(-0.3)  # Move backwards using negative velocity
                backward_event.clear()  # Reset the event after executing backward motion
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

def Movement_Comand():
    global emergency_event, forward_event, backward_event, left_event, right_event
    while True:
        pred = predict_frame()
        prediction = str(pred)
        if prediction == '[0]':
            print("Stay Hovering")
            pass
        elif prediction == '[5]':
            print("GO Right")
            right_event.set()
        elif prediction == '[1]':
            print("GO Left")
            left_event.set()
        elif prediction == '[2]':
            print("GO Right")
            right_event.set()
        elif prediction == '[3]':
            print("GO Forward")
            forward_event.set()
        elif prediction == '[4]':
            print("GO Back")
            backward_event.set()
        time.sleep(0.1)  # Adjust sleep time as needed

# Main execution
if __name__ == '__main__':
    # Load the trained model
     
    with open('knn_model.pkl', 'rb') as f:
        pred = pickle.load(f)
    
    
    # Open the serial port
    ser = serial.Serial('COM12', 9600)

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
        
        ######################################################

        # Start reading commands from text file
        command_thread = threading.Thread(target=Movement_Comand)
        command_thread.start()

        # Execute the take-off and hover sequence
        take_off_and_hover(scf)
        
