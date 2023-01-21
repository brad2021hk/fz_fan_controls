import argparse

# Constants
address_length = 4  # Length of the fan module address
command_length = 6  # Length of the command.  

# Write the PWM encoding to the specified file.  It takes an integer in value, converts to binary and then writes a PWM encoding for each bit.  
# It starts with the MSB on the left.  
def writePWM(file, length, value):
    bits = [(value >> bit) & 1 for bit in range (length -1, -1, -1)]
    for bit in bits:
        if bit:
            file.write(bit_high)
        else:
            file.write(bit_low)

# Writes a complete fan command to the file in PWM format.  Starts with the leading 01b encoding and then writes
# the address, which is a 4-bit encoding, followed by 1-bit for the dimmer mode and a 6-bit command. 
# The command seems to associate 1 bit per button on the remote.  
def writeCommand(file, address, dim, command):
 
    # Leading 01b code
    file.write(leading_zero)
    file.write(bit_high)
    
    # Write Address
    writePWM(file, address_length, address)
    
    # Write single bit for Dimmer switch setting
    if dim:
        file.write(bit_high)
    else:
        file.write(bit_low)

    # write the command
    writePWM(file, command_length, command)


parser = argparse.ArgumentParser(description="Flipper Zero Simple Fan Command Generator")

parser.add_argument('-f', '--frequency',
        required=False,
        type=float,
        action='store',
        default=303.875,
        help="Radio Frequency in Mhz")

parser.add_argument('-n', '--name', 
        required=False,
        action='store',
        default="fan",
        help="Prefix String for output sub files")

parser.add_argument('-a', '--address', 
        required=False, 
        action='store',
        default="0xf", 
        help="Fan Module Address") # Associated with dip switches in canopy module and remote.  

parser.add_argument('-d', '--dimmer', 
        required=False, 
        action='store_true', 
        default = False, 
        help="Set the Dimmer bit in the command stream") # The remote seems to handle dimmer support by sending a bit indicating the device has a dimmable bulb.

parser.add_argument('-u', '--universal', 
        required=False, 
        action='store_true', 
        default=False, 
        help="Build a config file that transmits to all addresses. Address parameter will be ignored")

args = parser.parse_args()

# Calculate the transmit frequency from the command line argument
frequency = args.frequency * 1000000

subHeader = ["Filetype: Flipper SubGhz RAW File\n", "Version: 1\n", "Frequency: %d\n" % frequency, "Preset: FuriHalSubGhzPresetOok650Async\n", "Protocol: RAW\n"]

# Generates strings for high and low bit encodings used in sub file.
# Negative number is amount of time signal is low.  
# Positive number is amount of time signal is high
# For a cycle time like 1020us, a bit high will be encoded as driving the signal low for
# 340us and high for 680us.  This seems like a simple pwm encouding.  
cycleTime = 1020
bit_high = "-%d %d " % (cycleTime/3, cycleTime/1.5)
bit_low = "-%d %d " % (cycleTime/1.5, cycleTime/3)
leading_zero = "-%d %d " % (11500, cycleTime/3)

# Observed commands.  Each button on the remote has an associated bit in the 6-bit command field.  
# Encoding 0x04 does not do anything with my hardware.  Maybe it supports reverse or another feature
# on a different canopy module.  
command_list = [("high", 0x20), ("med", 0x10), ("low", 0x08), ("light", 0x01), ("off", 0x02)]

address = int(args.address, 16)
dimmer = int(args.dimmer)

# The outer loop generates a separate .sub file for each command time.  A total of 5 files will be generated.  
for each in command_list:
    f = open("%s_%s.sub" % (args.name, each[0]), 'w')

    f.writelines(subHeader)

    # This condition creates a file that sends the specified command to each of the 16 possible address encodings.  This useful for a brute force 
    # turn the fans off command.  
    if args.universal:
        for address in range(0,16):
            f.write("RAW_Data: ")
            # Write Fan Off Command 5 times
            for i in range(0, 5):
                writeCommand(f, int(address), dimmer, each[1])

            # Write No Button Command 3 times
            for i in range(0, 3):
                writeCommand(f, int(address), dimmer, 0x0)

            # Write a final end line
            f.write("\n")
    # This condition outputs sub files that send command to the specified address only.  
    else:
        f.write("RAW_Data: ")

        # Write Fan Off Command 5 times
        for i in range(0, 5):
            writeCommand(f, address, dimmer, each[1])

        # Write No Button Command 3 times
        for i in range(0, 3):
            writeCommand(f, 0x0, dimmer, 0x0)

        # Write a final end line
        f.write("\n")

    f.close()




