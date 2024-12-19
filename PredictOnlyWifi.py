import requests
import time
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import csv
import pickle

# ESP32 IP address and endpoint
ESP32_IP = "http://192.168.0.234/"

# Load the trained model
with open('trRF3.pkl', 'rb') as f:
    pred = pickle.load(f)

# Setup lists to store previous and live data
previous_data = []
live_data = []

# Initialize arrays for time, sensor values, and speed
num_readings = 600
time_stamp = np.zeros(num_readings)
values1 = np.zeros(num_readings)
values2 = np.zeros(num_readings)
values3 = np.zeros(num_readings)
values4 = np.zeros(num_readings)
speed1 = np.zeros(num_readings)
speed2 = np.zeros(num_readings)
speed3 = np.zeros(num_readings)
speed4 = np.zeros(num_readings)

# Create figure and axes for live plot
fig, (ax_value, ax_speed) = plt.subplots(2, 1, figsize=(8, 6))

# Setup for live value plot (sensor readings)
plot_line_value1, = ax_value.plot([], [], 'b', linewidth=2, label='Sensor 1')
plot_line_value2, = ax_value.plot([], [], 'g', linewidth=2, label='Sensor 2')
plot_line_value3, = ax_value.plot([], [], 'r', linewidth=2, label='Sensor 3')
plot_line_value4, = ax_value.plot([], [], 'y', linewidth=2, label='Sensor 4')
ax_value.set(xlabel='Time (seconds)', ylabel='Pressure (hPa)', title='Live Sensor Data')
ax_value.legend()
ax_value.grid(True)

# Setup for live speed plot
plot_line_speed1, = ax_speed.plot([], [], 'b', linewidth=2, label='Speed1')
plot_line_speed2, = ax_speed.plot([], [], 'g', linewidth=2, label='Speed2')
plot_line_speed3, = ax_speed.plot([], [], 'r', linewidth=2, label='Speed3')
plot_line_speed4, = ax_speed.plot([], [], 'y', linewidth=2, label='Speed4')
ax_speed.set(xlabel='Time (seconds)', ylabel='Speed (units/s)', title='Live Speed Plot')
ax_speed.legend()
ax_speed.grid(True)

start_time = datetime.now()

# Function to fetch data from ESP32 over WiFi
def fetch_data():
    try:
        response = requests.get(ESP32_IP)
        if response.status_code == 200:
            data = response.text.strip().splitlines()  # Get the data as a list of lines
            # Convert each line to a list of integers
            data = [list(map(float, line.split())) for line in data]
            return data
        else:
            print("Failed to fetch data.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Function to save data to CSV
def save_data(data):
    with open("sensor_data.csv", "a") as file:
        for line in data:
            file.write(" ".join(map(str, line)) + "\n")

# Function to update the plots and calculate speed
def update_plot(frame):
    global time_stamp, values1, values2, values3, values4, speed1, speed2, speed3, speed4

    # Record timestamp
    time_stamp[frame] = (datetime.now() - start_time).total_seconds()

    # Fetch data from ESP32
    data = fetch_data()
    if data:
        live_data.append(data[0])  # Keep the most recent round of data
        previous_data.append(data[0])  # Save to previous data as well

        # Extract values for sensors
        values1[frame] = data[0][0]
        values2[frame] = data[0][1]
        values3[frame] = data[0][2]
        values4[frame] = data[0][3]

        # Calculate speed (change in value over time)
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

        # Save the data to CSV
        save_data([data[0]])

        # Update plots
        plot_line_value1.set_data(time_stamp[:frame + 1], values1[:frame + 1])
        plot_line_value2.set_data(time_stamp[:frame + 1], values2[:frame + 1])
        plot_line_value3.set_data(time_stamp[:frame + 1], values3[:frame + 1])
        plot_line_value4.set_data(time_stamp[:frame + 1], values4[:frame + 1])

        plot_line_speed1.set_data(time_stamp[:frame + 1], speed1[:frame + 1])
        plot_line_speed2.set_data(time_stamp[:frame + 1], speed2[:frame + 1])
        plot_line_speed3.set_data(time_stamp[:frame + 1], speed3[:frame + 1])
        plot_line_speed4.set_data(time_stamp[:frame + 1], speed4[:frame + 1])

        # Make prediction based on the sensor speeds
        X = np.array([[speed1[frame], speed2[frame], speed3[frame], speed4[frame]]])
        prediction = pred.predict(X)
        print(f"Prediction: {prediction}")

        # Redraw the plots
        plot_line_value1.axes.relim()
        plot_line_value1.axes.autoscale_view()
        plot_line_value2.axes.relim()
        plot_line_value2.axes.autoscale_view()
        plot_line_value3.axes.relim()
        plot_line_value3.axes.autoscale_view()
        plot_line_value4.axes.relim()
        plot_line_value4.axes.autoscale_view()

        plot_line_speed1.axes.relim()
        plot_line_speed1.axes.autoscale_view()
        plot_line_speed2.axes.relim()
        plot_line_speed2.axes.autoscale_view()
        plot_line_speed3.axes.relim()
        plot_line_speed3.axes.autoscale_view()
        plot_line_speed4.axes.relim()
        plot_line_speed4.axes.autoscale_view()

    return plot_line_value1, plot_line_value2, plot_line_value3, plot_line_value4, plot_line_speed1, plot_line_speed2, plot_line_speed3, plot_line_speed4

# Set up animation for live updates
from matplotlib.animation import FuncAnimation
ani = FuncAnimation(fig, update_plot, frames=num_readings, blit=True)

# Show the plot
plt.show()
