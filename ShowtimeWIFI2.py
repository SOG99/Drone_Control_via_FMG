import requests
import time
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import csv
import logging
import sys
import pickle
import threading
from threading import Event
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
# ESP32 IP address
ESP32_IP = "http://192.168.0.234/"

# Crazyflie URI
URI = 'radio://0/80/2M/E7E7'
DEFAULT_HEIGHT = 0.4

# Load the trained model
with open('trRF3.pkl', 'rb') as f:
    pred = pickle.load(f)

# Initialize variables for sensor data and predictions
num_readings = 150
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

# Events for drone control
deck_attached_event = Event()
emergency_event = Event()
forward_event = Event()
backward_event = Event()
left_event = Event()
right_event = Event()

# Function to fetch data over WiFi
def fetch_data():
    try:
        response = requests.get(ESP32_IP)
        if response.status_code == 200:
            data = response.text.strip().splitlines()
            return [list(map(float, line.split())) for line in data]
        else:
            print("Failed to fetch data.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Function to process data and make predictions
def predict_frame():
    global time_stamp, values1, values2, values3, values4, speed1, speed2, speed3, speed4, frame
    time_stamp[frame] = (datetime.now() - start_time).total_seconds()

    data = fetch_data()
    if not data:
        return None

    values1[frame], values2[frame], values3[frame], values4[frame] = data[0]

    if frame > 0:
        delta_time = time_stamp[frame] - time_stamp[frame - 1]
        speed1[frame] = (values1[frame] - values1[frame - 1]) / delta_time
        speed2[frame] = (values2[frame] - values2[frame - 1]) / delta_time
        speed3[frame] = (values3[frame] - values3[frame - 1]) / delta_time
        speed4[frame] = (values4[frame] - values4[frame - 1]) / delta_time
    else:
        speed1[frame] = speed2[frame] = speed3[frame] = speed4[frame] = 0

    X = np.array([[speed1[frame], speed2[frame], speed3[frame], speed4[frame]]])
    prediction = pred.predict(X)
    print(f"Prediction: {prediction}")

    frame += 1
    return prediction

# Drone movement logic based on predictions
def Movement_Comand():
    while not emergency_event.is_set():
        pred = predict_frame()
        if pred is None:
            continue

        prediction = str(pred)
        if prediction == '[0]':
            print("Hovering")
        elif prediction == '[5]':
            print("Move Right")
            right_event.set()
        elif prediction == '[1]':
            print("Move Left")
            left_event.set()
        elif prediction == '[2]':
            print("Move Right")
            right_event.set()
        elif prediction == '[3]':
            print("Move Forward")
            forward_event.set()
        elif prediction == '[4]':
            print("Move Backward")
            backward_event.set()
        time.sleep(0.1)

# Function to handle drone take-off and movement
def take_off_and_hover(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        while not emergency_event.is_set():
            if forward_event.is_set():
                mc.forward(0.3)
                forward_event.clear()
            elif backward_event.is_set():
                mc.forward(-0.3)
                backward_event.clear()
            elif left_event.is_set():
                mc.left(0.3)
                left_event.clear()
            elif right_event.is_set():
                mc.right(0.3)
                right_event.clear()
            time.sleep(0.1)

# Main function
if __name__ == '__main__':
    # Initialize Crazyflie drivers
    cflib.crtp.init_drivers()

    # Connect to the Crazyflie
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        scf.cf.param.add_update_callback(group='deck', name='bcFlow2', cb=lambda _, value_str: deck_attached_event.set() if int(value_str) else None)
        time.sleep(1)

        if not deck_attached_event.wait(timeout=5):
            print('No flow deck detected!')
            exit(1)

        # Start the prediction and command thread
        command_thread = threading.Thread(target=Movement_Comand)
        command_thread.start()

        # Start drone take-off and hover logic
        take_off_and_hover(scf)
