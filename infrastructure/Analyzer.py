__author__ = 'ubuntu'

from scapy.all import * #for scapy
from os import system #for cmd commands
from time import sleep #for waiting between commands
import ExtraLayers #for the extra information added over my packets
import myPackets #for handling my packets
import sys
from uuid import  getnode as get_mac
import os
startTime=int(time.time())

def sendTopologyDiscoveryPacket(numberOfFlowEntries):
    """
    Send a message that activates the topology application in the controller and update the topology in the controller.
    :param numberOfFlowEntries: How many flow entries to use (Implemented 2 versions, 4 or 3).
    :return: -
    """

    # Create the packet with the number of flow entries as payload.
    packet = Ether(type = ExtraLayers.topologyHostType,src = ExtraLayers.topologyHostEtherMAC)/\
             ExtraLayers.Vlan()/ExtraLayers.ProbePacketPayload(MeasurementRound = numberOfFlowEntries)
    sendp(packet, iface=interface) # Send the packet.
    packet.show() # Print the packet for debugging.
    
def sendAppendRTPPacket(path, currentRTPID):
    """
    Send a message that activates the topology application in the controller and update the topology in the controller.
    :param numberOfFlowEntries: How many flow entries to use (Implemented 2 versions, 4 or 3).
    :return: -
    """

    # Create the packet with the number of flow entries as payload.
    data = ":$$:{0}|{1}".format( str(path), currentRTPID )
    packet = Ether(type = ExtraLayers.analyzeType, src = ExtraLayers.appendRTPMAC)/ExtraLayers.Vlan()/Raw(load=data)
    
    sendp(packet, iface=interface) # Send the packet.
    packet.show() # Print the packet for debugging.
    
    
def sendAnalyzePacket(data):
    """
    Send a packet to inform the controller that it should analyze the data.
    :param data: Information about the MPs.
    :return:
    """
    #The data contains raw data in the end with the info about the MPs
    packet = Ether(type = ExtraLayers.analyzeType,src = ExtraLayers.analyzeEtherMAC)/ExtraLayers.Vlan()/\
             ExtraLayers.ProbePacketPayload(MeasurementRound = measurementRound)/Raw(load=data)
    sendp(packet, iface=interface) #send the packet
    packet.show() #print the packet for debugging

    

def sendProbePacket(numberOfPackets, interval):
    """
    Send the probe packets for RTT measurements.
    :param numberOfPackets: Number of packets to send.
    :param interval: Interval between packets.
    :return: -
    """

    global measurementRound
    count = 0

    # Send given number of packets.
    while (count < numberOfPackets):
        if count == 25:
            os.system("sshpass -p user scp -l 10000 ~/file user@14.2:/tmp/ &")
            print "SCP Started"
        if count == 75:
            os.system("killall sshpass &")
            print "SCP Killed"    
        #Construct the packet with the measurement round as payload.
        packet = Ether(type = ExtraLayers.VLAN_ETHERTYPE, src = ExtraLayers.DistributeMAC, dst = getSenderMac())/ExtraLayers.Vlan()/\
                 ExtraLayers.ProbePacketPayload(MeasurementRound = measurementRound)
        sendp(packet, iface=interface) # Send the packet.
        packet.show() # Print the packet for debugging.
        sleep((float)(interval)/1000) # Sleep for given amount of times
        measurementRound += 1
        count += 1


#Get the sender mac with given
def getSenderMac():
    return ':'.join(['{:02x}'.format((get_mac() >> i) & 0xff) for i in range(0,8*6,8)][::-1])


"""
Analyze the return probe packets.
Usage:
    present the RTTs - "p"
"""

def input_thread(user_input_list):
    """
    Listen to user input and add result to list.
    To be used as a separate thread.
    :param user_input_list: User input list.
    :return: -
    """
    while (1):
        l = raw_input()
        user_input_list.append(l)

# Set the interface (if given set it to be the given, if not the default is h1)
if (1 == len(sys.argv)):
    interface = "h1-eth0"
else:
    interface = sys.argv[1] 

# Temporary file to save the info.
fileName = "/home/user/MyProject/captures/tempPackets" + sys.argv[1]+ ".cap"
system("sudo rm -rf "+fileName) # Remove the file if exists.
# Sniff the packets in libpcap format in the background into the file with given file name.
system("dumpcap -i "+interface+" -w "+fileName+" -P -q &")


# Wait for 1 second.
time.sleep(1);

# Create a list of user commands.
user_commands = []

# Create thread that listen to user commands.
thread.start_new_thread(input_thread, (user_commands,))

# Set a file reader
a = PcapReader(fileName)
pcapFile = a.f
# Create packet lists
sniffedPackets = myPackets.myPacketHandler()

measurementRound = 1 # Initial measurement round number.,
currentRTPID = 1
currPos = pcapFile.tell() # Save current position
hdr = pcapFile.read(16) # Read the header
while (1):
    # Get command parameters.
    command_params = ''.join(user_commands).split(" ")

    # If the command is not empty
    if user_commands:
        # Case 's'  - Send a probe packet.
        # Usage: s <number of packet (default 1)> <interval (default 1000ms)>"
        if 's' == command_params[0]:
            interval = 1000
            numberOfPackets = 1

            #The second parameter is the number of packets to send.
            if (2 <= len(command_params)):
                numberOfPackets = int(command_params[1])

            #The third parameter is the interval between the probe packets in ms.
            if (3 == len(command_params)):
                interval = int(command_params[2])

            #Send the packet(s) with given interval.
            sendProbePacket(numberOfPackets, interval)

        # Case 'a'  - Send analysis packet and build the overlay network by installing the flow entries.
        # Usage: "a <number of MPs (default 1)> <MP 1(default (1)> .. <MP n>"
        elif 'a' == command_params[0]:

            # If no MPs are given save the defaults, otherwise save the number of MPs and list of given MPs.
            if (1 < len(command_params)):
                numberOfMPs = command_params[1]
                MPs = []
            else:
                numberOfMPs = "1"
                MPs = ['1']

            # Set the list of given MPs.
            pos = 2
            while  (pos < len(command_params)):
                MPs.append(command_params[pos])
                pos += 1

            # Prepare the data that need to be added to the analyzing packet.
            dataToAdd = ExtraLayers.createMPsData(numberOfMPs,MPs)

            # Send the packet to the controller.
            sendAnalyzePacket(dataToAdd)

        # Case 't'  - Send topology discovery packet and save the number of flow entries used..
        # Usage: "t <number of flow entries (default 4)>"

        elif 't' == command_params[0]:

            # The number of flow entries will be 3 if has more then single parameter in the command.
            if (1 < len(command_params)):
                numberOfFlowEntries = 3
            else:
                numberOfFlowEntries = 4

            # Send the packet to the controller.
            sendTopologyDiscoveryPacket(numberOfFlowEntries)

            print "sent topo packet with " , numberOfFlowEntries , "flow entries."

            
        elif 'r' == command_params[0]:
            RTPPath = []
            for switchID in command_params[1:]:
                RTPPath.append(int(switchID))
            
            sniffedPackets.rtps.paths[currentRTPID] = RTPPath 
            sendAppendRTPPacket(RTPPath, currentRTPID)
            currentRTPID = currentRTPID + 1
        # If p is pressed print all the info about the packets.
        elif 'p' == command_params[0]:
            sniffedPackets.printAllInfo()
        # Remove the last string that was entered.
        user_commands.pop(0)

    # If the header is too short or doesnt exist it means there is no packet.
    if (len(hdr) < 16):
        sleep (0.1)
    # If packet exists (with correct header size).
    else:
        sec,uSec,capLen,wireLen = struct.unpack(a.endian+"IIII", hdr) #Parse the header.
        #Analyze only packets with capLen equal to my packet capLen.
        sec,uSec,capLen,wireLen = struct.unpack(a.endian+"IIII", hdr) #Parse the header.
        
        
        sec = sec - startTime
        
        #Analyze only packets with capLen equal to my packet capLen.
        packet = pcapFile.read(capLen) # Read the packet from the file.
        sniffedPackets.handlePacket(packet,sec,uSec) # Handle the packet by adding it to reference packet 
        currPos = pcapFile.tell() # Save the current position
    hdr = pcapFile.read(16) #  Read the header

    
    
