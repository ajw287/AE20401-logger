import serial.tools.list_ports
import serial
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime
import threading
import queue
import numpy as np
from time import sleep


# Function to fetch available COM ports
def fetch_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

# Function to parse and process the serial data
def parse_data(line):
    # Modify this function to parse and process your serial data
    # Example: <ECN>:<CODE>:<DATA>
    parts = line.split(":")
    if len(parts) == 4:
        ecn = parts[0]
        code = parts[1]
        data = float(parts[2])
        return ecn, code, data
    return None, None, None

# Function to update the graph
def update_graph():
    timestamps = [entry[0] for entry in data_list]
    data = [entry[3] for entry in data_list]
    plt.clf()
    plt.plot(timestamps, data, marker='x')
    if len(timestamps) >10:
        tick_size = int(len(timestamps)/10)
        plt.xticks(timestamps[::tick_size])
    plt.xlabel("Time")
    plt.ylabel("Counts")
    plt.title("Serial Data Graph")
    plt.grid(True)
    plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better visibility
    canvas.draw()

# Function to save data to a CSV file
def save_to_csv():
    global data_list
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if file_path:
        with open(file_path, 'w') as file:
            file.write("Timestamp, ECN, Code, Data\n")
            for entry in data_list:
                timestamp, ecn, code, data = entry
                file.write(f"{timestamp},{ecn},{code},{data}\n")

# Function to read data from the selected COM port (in a separate thread)
def read_serial_data_in_thread(ser, stop_event, data_queue):
    global root
    charLim = 25
    chars = 0
    syncd = False
    while (syncd == False) and charLim > chars:
        serial_char = ser.read(1)
        print(serial_char)
        chars += 1
        if serial_char == b";":
            print("match!")
            syncd = True
    if(syncd == False):
        print("something went wrong with the syncing...")
        exit()
    try:
        while not stop_event.is_set():
            #line = ser.readline().decode().strip()
            line = ser.read(6).decode("utf-8")
            serial_char = b"x"
            while serial_char != ";":
                serial_char = ser.read(1).decode("utf-8")
                line += serial_char
            #print("serial data:")
            #print(line)
            ecn, code, data = parse_data(line)
            #print('device:%s code:%s data:$%.2f' % (ecn, code, data))
            if ecn is not None:
                timestamp = datetime.now().strftime('%H:%M:%S.%f')  # Generate timestamp for the line
                #data_list.append([timestamp, ecn, code, data])
                data_queue.put((timestamp, ecn, code, data))
    except serial.SerialException as e:
        print("Error:", e)
    # Call process_received_data again after a short delay, passing the data_queue as an argument
    #finally:
    #    if ser.is_open:
    #        ser.__del__()
    #
    

# Function to handle the "Start" button click
def start_button_click():
    global thread_stop_event, start_button, stop_button, serialCon, data_list, data_queue, read_thread

    start_button["state"] = "disabled"
    stop_button["state"] = "active"

    selected_port = com_port_var.get()
    if selected_port:
        try:
            ser = serial.Serial(selected_port, baudrate=9600, timeout=1)
            # Clear data_list before starting a new data acquisition
            data_list.clear()
            # Create a queue to hold the received data
            data_queue = queue.Queue()
            # Start a new thread to read data from the serial port
            read_thread = threading.Thread(target=read_serial_data_in_thread, args=(ser, thread_stop_event, data_queue))
            #thread = threading.Thread(target=read_serial_data_in_thread, args=(selected_port, thread_stop_event))
            read_thread.daemon = True  # Set the thread as a daemon so that it will stop when the main thread stops
            read_thread.start()
            # Update the graph when new data arrives
            root.after(100, process_received_data, data_queue)
            serialCon = ser
        except:
            print("Error connecting to serial")

# Function to process received data from the queue and update the graph
def process_received_data(data_queue):
    global data_list, thread_stop_event
    try:
        while True:
            timestamp, ecn, code, data = data_queue.get_nowait()
            data_list.append([timestamp, ecn, code, data])
    except queue.Empty: 
        pass
    update_graph()
    if not thread_stop_event.is_set():
        root.after(100, process_received_data, data_queue)  # Schedule the function to be called again after a delay
    
def stop_button_click():
    global start_button, stop_button, serial
    stop_button["state"] = "disabled"
    start_button["state"] = "active"
    stop_data_acquisition()
    

# Function to stop the data acquisition thread
def stop_data_acquisition():
    global serialCon, read_thread, thread_stop_event
    print("set stop event")
    thread_stop_event.set()
    sleep(0.15) # blocking wait for the last 'after' command
    print("waiting for thread to stop")
    if read_thread is not None:
        read_thread.join()  # Wait for the thread to terminate gracefully
        print("successful")
    if serialCon is not None:
       serialCon.__del__() #

# Function to handle the window closing event
def on_closing():
    stop_data_acquisition()
    root.destroy()
    sleep(0.5)
    exit()


### GLOBALS ###
# List to hold the received data
data_list = []
data_queue = None
# create a thread as a global
read_thread = None
# global for holding the serial connection.
serialCon = None

# Main function to create the GUI and start the application
def main():
    global root, canvas, data_list, thread_stop_event, read_thread, data_queue, start_button, stop_button, com_port_var
    # Create the main window
    root = tk.Tk()
    root.title("Serial Data Parser")

    # Event to stop the data acquisition thread when the window is closed
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Create the toolbar along the top
    toolbar = ttk.Frame(root)
    toolbar.pack(side=tk.TOP, fill=tk.X)

    # Fetch available COM ports
    com_ports = fetch_serial_ports()
    com_port_var = tk.StringVar(value=com_ports[0]) if com_ports else tk.StringVar()
    com_port_dropdown = ttk.Combobox(toolbar, textvariable=com_port_var, values=com_ports, state="readonly")
    com_port_dropdown.pack(side=tk.LEFT, padx=5, pady=5)

    start_button = ttk.Button(toolbar, text="Start", command=start_button_click)
    start_button.pack(side=tk.LEFT, padx=5, pady=5)

    stop_button = tk.Button(toolbar, text="Stop", command=stop_button_click)
    stop_button.pack(side=tk.LEFT, padx=5)
    stop_button["state"] = "disabled"


    save_button = ttk.Button(toolbar, text="Save to CSV", command=save_to_csv)
    save_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Create the main frame for the left and right sections
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Create the left frame for interface items
    left_frame = ttk.Frame(main_frame, width=200)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    left_frame.pack_propagate(False)  # Disable automatic resizing of the left frame

    # Interface items (example: radio buttons and check boxes)
    radio_var = tk.IntVar()
    radio_var.set(1)
    radio1 = tk.Radiobutton(left_frame, text="Option 1", variable=radio_var, value=1)
    radio2 = tk.Radiobutton(left_frame, text="Option 2", variable=radio_var, value=2)

    check_var1 = tk.BooleanVar()
    check_var2 = tk.BooleanVar()
    check_box1 = ttk.Checkbutton(left_frame, text="Checkbox 1", variable=check_var1, onvalue=True, offvalue=False)
    check_box2 = ttk.Checkbutton(left_frame, text="Checkbox 2", variable=check_var2, onvalue=True, offvalue=False)

    radio1.grid(row=0, sticky=tk.W)
    radio2.grid(row=1, sticky=tk.W)
    check_box1.grid(row=2, sticky=tk.W)
    check_box2.grid(row=3, sticky=tk.W)

    # Create the right frame for the graph
    right_frame = ttk.Frame(main_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Create the graph
    plt.figure(figsize=(7, 5))  # Adjust the figure size as needed
    plt.xlabel("Time")
    plt.ylabel("Data")
    plt.title("Serial Data Graph")
    plt.grid(True)
    canvas = FigureCanvasTkAgg(plt.gcf(), master=right_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # Make the graph fill the available space

    # Create an event to stop the data acquisition thread
    thread_stop_event = threading.Event()
    # Start the main loop
    root.mainloop()


# Run the main function when the script is executed
if __name__ == "__main__":
    main()