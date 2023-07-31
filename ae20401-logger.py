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
from parsers.data_parser import parse_data_message, message_format

# Function to fetch available COM ports
def fetch_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

# Function to update the graph
def update_graph():
    first_code = data_list[0][2]
    if first_code == 'C':
        if all(char == first_code for char in data_list[:][2]):
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

# Function to send a command down the serial port
def send_command(ser, command, data):
    if command == 'P':
        ser.send(f"401:{command}:{data}:;")
    elif command == 'Q':
        ser.send(f"401:{command}:{int(data*1000)}:;")
    else:
        pass

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
            # Note that timestamps aren't strict, but at the whims of python/OS
            timestamp = datetime.now().strftime('%H:%M:%S.%f')  # Generate timestamp for the line
            serial_char = b"x"
            while serial_char != ";":
                serial_char = ser.read(1).decode("utf-8")
                line += serial_char
            #print("serial data:")
            #print(line)
            message_contents = parse_data_message(line) 
            #print('device:%s code:%s data:$%.2f' % (ecn, code, data))
            if len(data) == 3:
                ecn, code, data = message_contents
                #data_list.append([timestamp, ecn, code, data])
                data_queue.put((timestamp, ecn, code, data))
            else:
                print(message_contents)
                raise ValueError("Received an unexpected or unimplemented serial message.")
    except serial.SerialException as e:
        print("Error:", e)
    
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

# Function to update the interface items based on the selected option
def update_interface_on_channel_change():
    global option_var, modes, left_frame, power_modes
    global checkbox_1_edge, checkbox_2_smooth
    global checkbox_3_offset, checkbox_4_run
    global checkbox_5_external, checkbox_6_imp_count
    global window_width
    global attenuation_text, offset_text, offset_scale_text, impulse_per_revolution_text

    selected_option = option_var.get()
    # Clear any existing widgets in the left pane
    for widget in left_frame.winfo_children():
        widget.destroy()

    # Add new widgets based on the selected option
    if selected_option == "Channel A":
        # Add UI options for Channel A
        radio_var = tk.StringVar(value="1")
        for i in range(3):
            radio_button = ttk.Radiobutton(left_frame, text=f"{modes[i]}", variable=radio_var, value=str(i+1))
            radio_button.pack(anchor=tk.W)

        checkbox1 = ttk.Checkbutton(left_frame, text="Rising Edge", variable=checkbox_1_edge)
        checkbox1.pack(anchor=tk.W)
        checkbox2 = ttk.Checkbutton(left_frame, text="Smooth Enabled", variable=checkbox_2_smooth)
        checkbox2.pack(anchor=tk.W)
        checkbox3 = ttk.Checkbutton(left_frame, text="Offset Enabled", variable=checkbox_3_offset)
        checkbox3.pack(anchor=tk.W)
        # Add a text frame and a button on the same line
        offset_magn_frame = ttk.Frame(left_frame)
        offset_magn_frame.pack(anchor=tk.W)
        label1 = ttk.Label(offset_magn_frame, text="Offset: (Hz)")
        label1.grid(row=0, column=0, columnspan=2, padx=2, pady=5)
        offset_text.set("0")
        offset_entry = ttk.Entry(offset_magn_frame, textvariable=offset_text, width=int(window_width/150), state='disabled')
        offset_entry.grid(row=1, column=0, padx=2, pady=5)
        button1 = ttk.Button(offset_magn_frame, text="Send", width=window_width*0.05)
        button1.grid(row=1, column=1, padx=2, pady=5)
        button1["state"] = "disabled"
        
        offset_scale_frame = ttk.Frame(left_frame)
        offset_scale_frame.pack(anchor=tk.W)
        label2 = ttk.Label(offset_scale_frame, text="Offset Scale:(min 0.001)")
        label2.grid(row=0, column=0, columnspan=2, padx=2, pady=5)
        offset_scale_text.set("1.000")
        offset_scale_entry = ttk.Entry(offset_scale_frame, textvariable=offset_scale_text, width=int(window_width/150), state='disabled')
        offset_scale_entry.grid(row=1, column=0, padx=2, pady=5)
        button2 = ttk.Button(offset_scale_frame, text="Send", width=window_width*0.05)
        button2.grid(row=1, column=1, padx=2, pady=5)
        button2["state"] = "disabled"

        checkbox4 = ttk.Checkbutton(left_frame, text="Pulse per Rev Mode", variable=checkbox_4_imp_countA)
        checkbox4.pack(anchor=tk.W)

        offset_imprev_frame = ttk.Frame(left_frame)
        offset_imprev_frame.pack(anchor=tk.W) 
        label3 = ttk.Label(offset_imprev_frame, text="Impulses per rev.")
        label3.grid(row=0, column=0, columnspan=2, padx=2, pady=5)
        impulse_per_revolution_text.set("100")
        impulse_per_revolution_entry = ttk.Entry(offset_imprev_frame, textvariable=impulse_per_revolution_text, width=int(window_width/150), state='disabled')
        impulse_per_revolution_entry.grid(row=1, column=0, padx=2, pady=5)
        button3 = ttk.Button(offset_imprev_frame, text="Send", width=window_width*0.05)
        button3.grid(row=1, column=1, padx=2, pady=2)
        button2["state"] = "disabled"
        


    elif selected_option == "Channel B":
        # Add UI options for Channel B
        radio_var = tk.StringVar(value="1")
        for i in range(2):
            radio_button = ttk.Radiobutton(left_frame, text=f"{modes[i]}", variable=radio_var, value=str(i+1))
            radio_button.pack(anchor=tk.W)
        checkbox2 = ttk.Checkbutton(left_frame, text="Smooth Enabled", variable=checkbox_2_smooth)
        checkbox2.pack(anchor=tk.W)
        checkbox3 = ttk.Checkbutton(left_frame, text="Offset Enabled", variable=checkbox_3_offset)
        checkbox3.pack(anchor=tk.W)

        offset_magn_frame = ttk.Frame(left_frame)
        offset_magn_frame.pack(anchor=tk.W)
        label1 = ttk.Label(offset_magn_frame, text="Offset: (Hz)")
        label1.grid(row=0, column=0, columnspan=2, padx=2, pady=5)
        offset_text.set("0")
        offset_entry = ttk.Entry(offset_magn_frame, textvariable=offset_text, width=int(window_width/150), state='disabled')
        offset_entry.grid(row=1, column=0, padx=2, pady=5)
        button1 = ttk.Button(offset_magn_frame, text="Send", width=window_width*0.05, command=lambda: send_command('P', offset_text))
        button1.grid(row=1, column=1, padx=2, pady=5)
        button1["state"] = "disabled"
        
        offset_scale_frame = offset_magn_frame
        #offset_scale_frame = ttk.Frame(left_frame)
        #offset_scale_frame.pack(anchor=tk.W)
        label2 = ttk.Label(offset_scale_frame, text="Offset Scale:(min 0.001)")
        label2.grid(row=3, column=0, columnspan=2, padx=2, pady=5)
        offset_scale_text.set("1.000")
        offset_scale_entry = ttk.Entry(offset_scale_frame, textvariable=offset_scale_text, width=int(window_width/150), state='disabled')
        offset_scale_entry.grid(row=4, column=0, padx=2, pady=5)
        button2 = ttk.Button(offset_scale_frame, text="Send", width=window_width*0.05)
        button2.grid(row=4, column=1, padx=2, pady=5)
        button2["state"] = "disabled"

    elif selected_option == "Channel C":
        # Add radio buttons for Option 3
        checkbox5 = ttk.Checkbutton(left_frame, text="Run/Stop", variable=checkbox_5_run)
        checkbox5.pack(anchor=tk.W)
        checkbox6 = ttk.Checkbutton(left_frame, text="Internal/External", variable=checkbox_6_external)
        checkbox6.pack(anchor=tk.W)
        checkbox7 = ttk.Checkbutton(left_frame, text="Pulse per Rev Mode", variable=checkbox_7_imp_countC)
        checkbox7.pack(anchor=tk.W)
        offset_imprev_frame = ttk.Frame(left_frame)
        offset_imprev_frame.pack(anchor=tk.W)
        label3 = ttk.Label(offset_imprev_frame, text="Impulses per revolution")
        label3.grid(row=0, column=0, columnspan=2, padx=2, pady=5)
        impulse_per_revolution_text.set("100")
        impulse_per_revolution_entry = ttk.Entry(offset_imprev_frame, textvariable=impulse_per_revolution_text, width=int(window_width/150), state='disabled')
        impulse_per_revolution_entry.grid(row=1, column=0, padx=2, pady=5)
        button3 = ttk.Button(offset_imprev_frame, text="Send", width=window_width*0.05)
        button3.grid(row=1, column=1, padx=2, pady=2)
        button3["state"] = "disabled"
            
    elif selected_option == "Power":
        # Add radio buttons for Option 3
        radio_var = tk.StringVar(value="A")
        for i in range(len(power_modes)):
            radio_button = ttk.Radiobutton(left_frame, text=f"mode: {power_modes[i]}", variable=radio_var, value=chr(65+i))
            radio_button.pack(anchor=tk.W)
        
        checkbox8 = ttk.Checkbutton(left_frame, text="Attenuator", variable=checkbox_8_attenuator)
        checkbox8.pack(anchor=tk.W)
        # Add a text frame and a button on the same line
        text_btn_frame = ttk.Frame(left_frame)
        text_btn_frame.pack(anchor=tk.W)
        label = ttk.Label(text_btn_frame, text="Att.: (dB)")
        label.grid(row=0, column=0, padx=5, pady=5)
        attenuation_text.set("0.0")
        attenuation_entry = ttk.Entry(text_btn_frame, textvariable=attenuation_text, width=int(window_width/150), state='disabled')
        attenuation_entry.grid(row=1, column=0, padx=2, pady=5)
        button = ttk.Button(text_btn_frame, text="Send", width=window_width*0.05)
        button.grid(row=1, column=1, padx=2, pady=2)
        button["state"] = "disabled"

def on_dropdown_select(event):
    update_interface_on_channel_change()

### GLOBALS ###
# List to hold the received data
data_list = []
data_queue = None
# create a thread as a global
read_thread = None
# global for holding the serial connection.
serialCon = None
channel_options = ["Channel A", "Channel B", "Channel C", "Power"]
channel_dropdown = None
left_frame = None
option_var = None
modes = ["Frequency","Period","RPM"]
power_modes=["dBm",  "mW", "Vrms","Peak-Peak (Vpp)", "Vpeak (Vp)"]
# menu mode checkboxes
checkbox_1_edge = None
checkbox_2_smooth = None
checkbox_3_offset = None
checkbox_4_imp_countA = None
checkbox_5_run = None
checkbox_6_external = None
checkbox_7_imp_countC = None
checkbox_8_attenuator = None
# mode menu text entries
attenuation_text = None
offset_text = None
offset_scale_text = None
impulse_per_revolution_text = None

window_width = 0

# Main function to create the GUI and start the application
def main():

    global root, canvas, data_list, thread_stop_event, read_thread, data_queue
    global start_button, stop_button, com_port_var, channel_dropdown, left_frame, option_var, channel_options
    global checkbox_1_edge, checkbox_2_smooth
    global checkbox_3_offset, checkbox_4_imp_countA, checkbox_5_run
    global checkbox_6_external, checkbox_7_imp_countC, checkbox_8_attenuator
    global attenuation_text, window_width
    global attenuation_text, offset_text, offset_scale_text, impulse_per_revolution_text

    # Create the main window
    root = tk.Tk()
    #initialise tkinter global variables
    checkbox_1_edge = tk.IntVar(value=0)
    checkbox_2_smooth = tk.IntVar(value=0)
    checkbox_3_offset = tk.IntVar(value=0)
    checkbox_4_imp_countA = tk.IntVar(value=0)
    checkbox_5_run = tk.IntVar(value=1)
    checkbox_6_external = tk.IntVar(value=1)
    checkbox_7_imp_countC = tk.IntVar(value=0)
    checkbox_8_attenuator = tk.IntVar(value=0)

    attenuation_text = tk.StringVar()
    offset_text = tk.StringVar()
    offset_scale_text = tk.StringVar()
    impulse_per_revolution_text = tk.StringVar()

    option_var = tk.StringVar(value="Channel C")

    root.title("Æ20401 Data Logger")

    # Event to stop the data acquisition thread when the window is closed
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Calculate the window size based on screen size
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = int(screen_width * 4 / 5)
    window_height = int(screen_height * 2 / 3)
    root.geometry(f"{window_width}x{window_height}")

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

    # Add the new dropdown to the toolbar
    #channel_options = ["Channel A", "Channel B", "Channel C"]
    channel_dropdown = ttk.Combobox(toolbar, textvariable=option_var, values=channel_options)#, state="readonly")
    channel_dropdown.pack(side=tk.LEFT, padx=5, pady=5)
    #option_var.set(channel_options[2])

    # Bind the dropdown's selection event to update the interface items
    channel_dropdown.bind("<<ComboboxSelected>>", on_dropdown_select)

    # Create the main frame for the left and right sections
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Create the left frame for interface items
    left_frame_width = window_width/5
    if left_frame_width < 300:
        left_frame_width = 300
    left_frame = ttk.Frame(main_frame, width=left_frame_width)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    left_frame.pack_propagate(False)  # Disable automatic resizing of the left frame

    # Interface items (example: radio buttons and check boxes)
    update_interface_on_channel_change()

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