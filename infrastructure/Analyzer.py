__author__ = 'ubuntu'

from scapy.all import * #for scapy
from os import system #for cmd commands
from time import sleep #for waiting between commands
import ExtraLayers #for the extra information added over my packets
import myPackets #for handling my packets
import sys


"""
Analyze the return probe packets.
Usage:
    present the RTTs - "p"
"""

def input_thread(L):
    """
    Listen to user input and add result to list.
    To be used as a separate thread.
    :param user_input_list: User input list.
    :return: -
    """
    while (1):
        l = raw_input()
        L.append(l)

# Set the interface (if given set it to be the given, if not the default is h1)
if (1 == len(sys.argv)):
    interface = "h1-eth0"
else:
    interface = sys.argv[1] + "-eth0"

# Temporary file to save the info.
fileName = "/home/ubuntu/MyProject/captures/tempPackets" + sys.argv[1]+ ".cap"
system("sudo rm -rf "+fileName) # Remove the file if exists.
# Sniff the packets in libpcap format in the background into the file with given file name.
system("dumpcap -i "+interface+" -w "+fileName+" -P -q &")

# Wait for 1 second.
time.sleep(1);

# Create new thread that listen to input
L = []
thread.start_new_thread(input_thread, (L,))
# Set a file reader
a = PcapReader(fileName)
pcapFile = a.f
# Create packet lists
sniffedPackets = myPackets.myPacketHandler()

currPos = pcapFile.tell() # Save current position
hdr = pcapFile.read(16) # Read the header
while (1):
    if L:
        # If p is pressed print all the info about the packets.
        if 'p' == L[0]:
            sniffedPackets.printAllInfo()
        # Remove the last string that was entered.
        L.pop(0)

    # If the header is too short or doesnt exist it means there is no packet.
    if (len(hdr) < 16):
        sleep (0.1)
    # If packet exists (with correct header size).
    else:
        sec,uSec,capLen,wireLen = struct.unpack(a.endian+"IIII", hdr) #Parse the header.
        #Analyze only packets with capLen equal to my packet capLen.

        if (32 == capLen):
            packet = pcapFile.read(capLen) # Read the packet from the file.
            sniffedPackets.handlePacket(packet,sec,uSec) # Handle the packet by adding it to reference packet list or return packet list
    currPos = pcapFile.tell() # Save the current position
    hdr = pcapFile.read(16) #  Read the header
