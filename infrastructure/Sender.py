from scapy.all import *
from uuid import  getnode as get_mac
import ExtraLayers
from time import sleep
import thread

''' Send packets according to user commands.
    First, use "t" to discover the topology, then use "a" to analyze the topology and install the flow entries
    representing the overlay network. After the overlay network was established use "s" to send to probe packets
    for network RTT measurements.
    Usage:
    Discover the network topology - "t <number of flow entries>"
    Establish the overlay network - "a <number of MPs> <MP 1> .. <MP  n>
    Send probe packet (for network RTT measurements) - "s <number of packet> <interval>"
    NOTE: The packets sent with 't' or 'a' are sent to one of the switches, then it will be sent to the controller
    since there is no corresponding flow entry for such a packet. This process can be automated in the controller
    but it is currently manual.
    '''


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



def user_commands_handler():
    """
    Wait for commands from user and handle them:
    :return: -
    """

    # Create a list of user commands.
    user_commands = []

    # Create thread that listen to user commands.
    thread.start_new_thread(input_thread, (user_commands,))

    # Runs infinite loop for commands handling.
    while True:

        # Get command parameters.
        command_params = ''.join(user_commands).split(" ")

        # If the command is not empty
        if command_params:

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

            if 't' == command_params[0]:

                # The number of flow entries will be 3 if has more then single parameter in the command.
                if (1 < len(command_params)):
                    numberOfFlowEntries = 3
                else:
                    numberOfFlowEntries = 4

                # Send the packet to the controller.
                sendTopologyDiscoveryPacket(numberOfFlowEntries)

                print "sent topo packet with " , numberOfFlowEntries , "flow entries."

            # pop the last command.
            if len(user_commands):
                user_commands.pop(0)

        # Wait for input again.
        sleep(0.1)

def sendTopologyDiscoveryPacket(numberOfFlowEntries):
    """
    Send a message that activates the topology application in the controller and update the topology in the controller.
    :param numberOfFlowEntries: How many flow entries to use (Implemented 2 versions, 4 or 3).
    :return: -
    """

    # Create the packet with the number of flow entries as payload.
    packet = Ether(type = ExtraLayers.topologyHostType,src = ExtraLayers.topologyHostEtherMAC)/\
             ExtraLayers.Vlan()/ExtraLayers.ProbePacketPayload(MeasurementRound = numberOfFlowEntries)
    sendp(packet) # Send the packet.
    packet.show() # Print the packet for debugging.

#
def sendAnalyzePacket(data):
    """
    Send a packet to inform the controller that it should analyze the data.
    :param data: Information about the MPs.
    :return:
    """
    #The data contains raw data in the end with the info about the MPs
    packet = Ether(type = ExtraLayers.analyzeType,src = ExtraLayers.analyzeEtherMAC)/ExtraLayers.Vlan()/\
             ExtraLayers.ProbePacketPayload(MeasurementRound = measurementRound)/Raw(load=data)
    sendp(packet) #send the packet
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
        #Construct the packet with the measurement round as payload.
        packet = Ether(type = ExtraLayers.VLAN_ETHERTYPE ,src = getSenderMac())/ExtraLayers.Vlan()/\
                 ExtraLayers.ProbePacketPayload(MeasurementRound = measurementRound)
        sendp(packet) # Send the packet.
        packet.show() # Print the packet for debugging.
        sleep((float)(interval)/1000) # Sleep for given amount of times
        measurementRound += 1
        count += 1


#Get the sender mac with given
def getSenderMac():
    return ':'.join(['{:02x}'.format((get_mac() >> i) & 0xff) for i in range(0,8*6,8)][::-1])


### Start of code.

measurementRound = 1 # Initial measurement round number.,
user_commands_handler()
