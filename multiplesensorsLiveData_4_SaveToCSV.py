import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime
import numpy as np
import csv


#Print AND PLOT

# Open the serial port
ser = serial.Serial('COM12', 9600)

# Create figure and axes for live plot
fig, (ax_value, ax_speed) = plt.subplots(2, 1, figsize=(8, 6))
plot_line_value1, = ax_value.plot([], [], 'b', linewidth=2, label='Sensor 1 R Tooth')
plot_line_value2, = ax_value.plot([], [], 'g', linewidth=2, label='Sensor 2 R EyeBrow')
plot_line_value3, = ax_value.plot([], [], 'r', linewidth=2, label='Sensor 3 L EyeBrow')
plot_line_value4, = ax_value.plot([], [], 'y', linewidth=2, label='Sensor 4 L Tooth')
ax_value.set(xlabel='Time (seconds)', ylabel='Value', title='Live Arduino Data Plot')
ax_value.legend()
ax_value.grid(True)

plot_line_speed1, = ax_speed.plot([], [], 'b', linewidth=2, label='Speed1 R Tooth')
plot_line_speed2, = ax_speed.plot([], [], 'g', linewidth=2, label='Speed2 R EyeBrow')
plot_line_speed3, = ax_speed.plot([], [], 'r', linewidth=2, label='Speed3 L EyeBrow')
plot_line_speed4, = ax_speed.plot([], [], 'y', linewidth=2, label='Speed4 L Tooth')
ax_speed.set(xlabel='Time (seconds)', ylabel='Speed', title='Live Speed Plot')
ax_speed.legend()
ax_speed.grid(True)

# Set up variables for live updating
num_readings = 60
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

# CSV file to save the data
#csv_filename = 'recorded_data_4sensors.csv'

# Function to update the plots and save data to CSV
def update_plot(frame):
    global time_stamp, values1, values2, values3, values4, speed1, speed2, speed3, speed4

    # Record timestamp
    time_stamp[frame] = (datetime.now() - start_time).total_seconds()

    # Receive data from Arduino
    data = ser.readline().decode().strip()

    # Convert received data to numeric format ((values are separated by spaces))
    values = list(map(float, data.split()))

    # Extract values
    values1[frame] = values[0]
    values2[frame] = values[1]
    values3[frame] = values[2]
    values4[frame] = values[3]

    # Calculate speed 
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

    # Display received data and speeds
    print(f'Time: {time_stamp[frame]:.2f} - Sensor1: {values1[frame]} - Sensor2: {values2[frame]} - Sensor3: {values3[frame]} - Sensor4: {values4[frame]} - Speed1: {speed1[frame]} - Speed2: {speed2[frame]} - Speed3: {speed3[frame]} - Speed4: {speed4[frame]}')

    # Update live value plots
    plot_line_value1.set_data(time_stamp[:frame + 1], values1[:frame + 1])
    plot_line_value1.axes.relim()
    plot_line_value1.axes.autoscale_view()

    plot_line_value2.set_data(time_stamp[:frame + 1], values2[:frame + 1])
    plot_line_value2.axes.relim()
    plot_line_value2.axes.autoscale_view()

    plot_line_value3.set_data(time_stamp[:frame + 1], values3[:frame + 1])
    plot_line_value3.axes.relim()
    plot_line_value3.axes.autoscale_view()

    plot_line_value4.set_data(time_stamp[:frame + 1], values4[:frame + 1])
    plot_line_value4.axes.relim()
    plot_line_value4.axes.autoscale_view()

    # Update live speed plots
    plot_line_speed1.set_data(time_stamp[:frame + 1], speed1[:frame + 1])
    plot_line_speed1.axes.relim()
    plot_line_speed1.axes.autoscale_view()

    plot_line_speed2.set_data(time_stamp[:frame + 1], speed2[:frame + 1])
    plot_line_speed2.axes.relim()
    plot_line_speed2.axes.autoscale_view()

    plot_line_speed3.set_data(time_stamp[:frame + 1], speed3[:frame + 1])   
    plot_line_speed3.axes.relim()
    plot_line_speed3.axes.autoscale_view()

    plot_line_speed4.set_data(time_stamp[:frame + 1], speed4[:frame + 1])
    plot_line_speed4.axes.relim()
    plot_line_speed4.axes.autoscale_view()

    # Save data to CSV
    with open('C:/Users/User/OneDrive/Desktop/Thesis/ExtraSet.csv', mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([time_stamp[frame], speed1[frame], speed2[frame], speed3[frame], speed4[frame]])

    # Stop plotting after reach num_readings
    if frame + 1 == num_readings:
        ani.event_source.stop()

    return plot_line_value1, plot_line_value2, plot_line_value3, plot_line_value4, plot_line_speed1, plot_line_speed2, plot_line_speed3, plot_line_speed4

# Plot Animation
ani = FuncAnimation(fig, update_plot, frames=num_readings, blit=True)

# Show plot
plt.show()

# Close the serial port
ser.close()
