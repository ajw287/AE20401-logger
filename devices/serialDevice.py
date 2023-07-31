
import serial.tools.list_ports
import serial
from datetime import datetime

from parsers.data_parser import parse_data_message, message_format

class serialDevice:

    ser = None
    data_queue = None
    connected = False
    synchronised = False
    charLim = 50

    def __init__(self, max_message_length=50):
        self.synchronised = False
        self.charLim = max_message_length

    def connect(self, selected_port):
        try:
            self.ser = serial.Serial(selected_port, baudrate=9600, timeout=1)
            # Clear data_list before starting a new data acquisition
            
            # Create a queue to hold the received data
            data_queue = queue.Queue()
            # Start a new thread to read data from the serial port
            read_thread = threading.Thread(target=read_serial_data_in_thread, args=(ser, thread_stop_event, data_queue))
            #thread = threading.Thread(target=read_serial_data_in_thread, args=(selected_port, thread_stop_event))
            read_thread.daemon = True  # Set the thread as a daemon so that it will stop when the main thread stops
            read_thread.start()
            # Update the graph when new data arrives
            root.after(100, process_received_data, data_queue)
            #serialCon = ser
            connected = True
        except:
            print("Error connecting to serial")

    def fetch_serial_ports(self):
        """ Function to fetch available COM ports

        Returns
        -------
        ports : list
            a list of available ports
        """

        return [port.device for port in serial.tools.list_ports.comports()]

    def send_command(self, command, data):
        """send a command down the serial port

        Parameters
        ----------
        ser : serial.serialposix.Serial
            an open serial port to the ae20401
        command: string
            string of the command to send (commands are found in data_parser.message_format)
        data:   string
            data to send with the command see ae20401 manual
        """

        if command == 'P':
            self.ser.send(f"401:{command}:{data}:;")
        elif command == 'Q':
            self.ser.send(f"401:{command}:{int(data*1000)}:;")
        else:
            pass
    
    def synchronise(self):
        """ Parse untill you get a ';' discard any partial message on start"""

        chars = 0
        try:    
            while (self.synchronised == False) and self.charLim > chars:
                serial_char = self.ser.read(1)
                #print(serial_char)
                chars += 1
                if serial_char == b";":
                    print("match!")
                    self.synchronised = True
            if(self.synchronised == False):
                print("something went wrong with the syncing...")
                exit()
        except serial.SerialException as e:
            print("Error:", e)
    
    def get_next_message(self):
        """ get the next text up to a ';' delimeter
        
        Returns
        -------
        timestamp
            an approximate timestamp from datetime
        ecn
            a string of the ECN (402 for the ae20401)
        code
            a string of the command code
        data
            a string of the data
        """
        try:
            line = ser.read(6).decode("utf-8")
            # Note that timestamps aren't strict, but at the whims of python/OS
            timestamp = datetime.now().strftime('%H:%M:%S.%f')  # Generate timestamp for the line
            serial_char = b"x"
            while serial_char != ";":
                serial_char = ser.read(1).decode("utf-8")
                line += serial_char
            message_contents = parse_data_message(line) 
            #print('device:%s code:%s data:$%.2f' % (ecn, code, data))
            if len(message_contents) == 3:
                ecn, code, data = message_contents
                #data_list.append([timestamp, ecn, code, data])
                #data_queue.put((timestamp, ecn, code, data))
                return timestamp, ecn, code, data
            else:
                print(message_contents)
                raise ValueError("Received an unexpected or unimplemented serial message.")
        except (serial.SerialException, ValueError) as e:
            print("Error:", e)
    
    def disconnect(self):
        try:
            if self.ser is not None:
                self.__del__() #
        except serial.SerialException as e:
            print("Error:", e)

