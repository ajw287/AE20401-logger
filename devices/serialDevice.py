
import serial.tools.list_ports
import serial
import queue
from datetime import datetime

from parsers.data_parser import parse_data_message, message_format

class serialDevice:

    ser = None
    data_queue = None # a temp store for passing data from the serial to the data_list in main
    connected = False
    synchronised = False
    charLim = 50

    def __init__(self, max_message_length=50):
        self.synchronised = False
        self.connected = False
        self.charLim = max_message_length
        self.data_queue =  queue.Queue()

    def connect(self, selected_port):
        # Create a queue to hold the received data
        try:
            self.ser = serial.Serial(selected_port, baudrate=9600, timeout=1)
            self.connected = True
        except Exception as e:
            print(e)
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

        if command is not None:
            #print("c: "+command + "   d:" + str(data))
            simple_commands = ('E', 'F', 'G', 'H', 'I', 'J' , 
                                'L', 'M', 'N', 'O', 'P', 
                                'R', 'S', 'T', 'U', 'Y','Z')
            float_commands = ('K','Q')
            #print(type(command))
            if self.connected:
                if command.startswith(simple_commands):
                    data = int(data)
                    cmd_str = f"401:{command}:{data}:;"
                    cmd_ascii = cmd_str.encode(encoding="ascii",errors="ignore")
                    #print(cmd_ascii)
                    self.ser.write(cmd_ascii)
                elif command.startswith(float_commands):
                    data = int(float(data) *1000)
                    cmd_str = f"401:{command}:{data}:;"
                    cmd_ascii = cmd_str.encode(encoding="ascii",errors="ignore")
                    #print(cmd_ascii)
                    self.ser.write(cmd_ascii)
                return

                if command == 'P':
                    self.ser.write(f"401:{command}:{data}:;")
                elif command == 'Q':
                    self.ser.write(f"401:{command}:{int(data*1000)}:;")
                else:
                    pass
            else:
                pass # ignore commands when unconnected
    
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
            line = self.ser.read(6).decode("utf-8")
            # Note that timestamps aren't strict, but at the whims of python/OS
            timestamp = datetime.now().strftime('%H:%M:%S.%f')  # Generate timestamp for the line
            serial_char = b"x"
            while serial_char != ";":
                serial_char = self.ser.read(1).decode("utf-8")
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
            self.connected = False
            self.synchronised = False
            if self.ser is not None:
                self.ser.__del__() #
        except serial.SerialException as e:
            print("Error:", e)

