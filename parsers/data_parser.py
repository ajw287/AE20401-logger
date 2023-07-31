

# Define the arrow direction mapping
message_format = {
    'A': ('dev_to_pc',  'Frequency Channel A',              'in nHz',),
    'B': ('dev_to_pc',  'Frequency Channel B',              'in uHz',),
    'C': ('dev_to_pc',  'Counter Channel C',                'in Count',),
    'D': ('dev_to_pc',  'Power Channel PWR',                'in 0.1dBm',),
    'E': ('bi_dir',     'Current Channel',                  '0 = A, 1 = B, 2 = C, 3 = PWR',),
    'F': ('bi_dir',     'Channel A: Mode',                  '0 = FREQ, 1 = PER, 2 = RPM',),
    'G': ('bi_dir',     'Channel A: Rising/Falling Edge',   '0 = Rising, 1 = Falling',),
    'H': ('bi_dir',     'Channel A: Smooth Enabled?',       '0 = FALSE, 1 = TRUE',),
    'I': ('bi_dir',     'Channel A: Offset Enabled?',       '0 = FALSE, 1 = TRUE',),
    'J': ('bi_dir',     'Channel A: Offset Value',          'in Hz',),
    'K': ('bi_dir',     'Channel A: Offset Scale',          'in x0.001',),
    'L': ('bi_dir',     'Channel A: Imp/Rev',               'in x1',),
    'M': ('bi_dir',     'Channel B: Mode',                  '0 = FREQ, 1 = PER',),
    'N': ('bi_dir',     'Channel B: Smooth Enabled?',       '0 = FALSE, 1 = TRUE',),
    'O': ('bi_dir',     'Channel B: Offset Enabled?',       '0 = FALSE, 1 = TRUE',),
    'P': ('bi_dir',     'Channel B: Offset Value',          'in Hz',),
    'Q': ('bi_dir',     'Channel B: Offset Scale',          'in x0.001',),
    'R': ('bi_dir',     'Channel C: RUN/STOP',              '0 = STOP, 1 = RUN',),
    'S': ('bi_dir',     'Channel C: Source',                '0 = INT, 1 = EXT',),
    'T': ('bi_dir',     'Channel C: Imp/Count',             'in x1',),
    'U': ('bi_dir',     'Channel PWR: Mode',                '0 = dBm, 1 = mW, 2 = Vrms, 3 = Vpp, 4 = Vp',),
    'V': ('bi_dir',     'Channel PWR: Attenuator Enabled?', '0 = FALSE, 1 = TRUE',),
    'W': ('bi_dir',     'Channel PWR: Attenuator Value',    'in 0.1dB',),
    'X': ('bi_dir',     'Channel PWR: Freq AE204015',       '0 = 1 MHz, 1 = 100 MHz, 2 = 200 MHz ...',),
    'Y': ('bi_dir',     'Decimal Point',                    '0 = \',\' 1 = \'.\'',),
    'Z': ('to_dev',     'Channel C: Reset',),
    '1': ('dev_to_pc',  'Modules Installed?',               '0 = none, 1 = AE204017, 2 = AE204015, 3 = AE204017+AE204015, 4 = AE204014, 5 = AE204017+AE204014',),
    '2': ('dev_to_pc',  'Hardware Rev.',),
    '3': ('dev_to_pc',  'Firmware Rev.',),
    '4': ('dev_to_pc',  'Product ID',),
    '5': ('bi_dir',     'Channel PWR: Freq AE204014',       '0 = 10 MHz, 1 = 1 GHz, 2 = 2 GHz ...',),
    '6': ('bi_dir',     'Reserved',),
    '7': ('bi_dir',     'Reserved',),
    '8': ('bi_dir',     'Reserved',),
    '9': ('bi_dir',     'Reserved',),
    '0': ('pc_to_dev',  'Get All Settings'),
}

def parse_data_message(data_message):
    # Split the data_message into its components
    components = data_message.strip(';').split(':')
    # Process
    l = len(components)
    if l == 3:
        ecn, code, data = components
    elif l == 4 and components[0] == "":
        waste, ecn, code, data = components
    elif l == 4 and components[3] == "":
        ecn, code, data, waste = components
    else:
        print(components)
        return "Unexpected number components in the message"
    
    # Check if the ECN is 401 as it is always expected for this device
    if ecn != '401':
        return "Invalid ECN"
    
    # Check if the code is in the message_format
    if code not in message_format:
        return "Invalid CODE"

    return ecn, code, data

# Example usage:
if __name__ == "__main__":
    data_message = "401:C:0"
    result = parse_data_message(data_message)
    print(result)
    test_list = (   ["401:C:0",("401","C","0")],
                ["402:C:501988010", ("401","C","501988010")],
            )
    for i, test_command in enumerate(test_list):
            print(test_command)
            print(i)
            result = parse_data_message(test_command[0])
            for r, e in zip(result, test_command[1]):
                print(r)
                print(e)
            #for data_message, e1,e2,e3  in (test_command[0], test_command[1]):
            #    print("dm")
            #    print(data_message)
            #    print("e")
            #    print(expected)
            #    result = parse_data_message(data_message)
