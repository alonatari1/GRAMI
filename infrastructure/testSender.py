__author__ = 'ubuntu'

from scapy.all import * #for scapy
from time import sleep #for waiting between commands
import thread
import ExtraLayers #for the extra information added over my packets
import sys
from os import system
from uuid import  getnode as get_mac #getting MAC

#Send the packet that should be distributed
def sendProbePackets(numberOfPackets, interval):
    global measurementRound
    count = 0
    #Send given number of packets
    while (count < numberOfPackets):
        #construct the packet with my extra layer
        packet = Ether(type = ExtraLayers.VLAN_ETHERTYPE ,src = getSenderMac())/ExtraLayers.Vlan()/ExtraLayers.ProbePacketPayload(ID = packetId)
        print packetId
        sendp(packet) #send the packet
        sleep((float)(interval)/1000) #Sleep for given amount of times
        packetId += 1 #increase the packet id
        count += 1

#Send a packet that will make the controller analyze the data
def sendAnalyzePacket(data):
    #The data contains raw data in the end with the info about the MPs
    packet = Ether(type = ExtraLayers.analyzeType,src = ExtraLayers.analyzeEtherMAC)/ExtraLayers.Vlan()/ExtraLayers.ProbePacketPayload(ID = measurementRound)/Raw(load=data)
    sendp(packet) #send the packet
    packet.show() #print the packet for debugging

def sendTopologyDiscoveryPacket(numberOfRules):
    '''send a message that will update the topology in the controller'''
    packet = Ether(type = ExtraLayers.topologyHostType,src = ExtraLayers.topologyHostEtherMAC)/ExtraLayers.Vlan()/ExtraLayers.ProbePacketPayload(ID = numberOfRules)
    sendp(packet) #send the packet
    packet.show() #print the packet for debugging


#Get the sender mac with given
def getSenderMac():
    return ':'.join(['{:02x}'.format((get_mac() >> i) & 0xff) for i in range(0,8*6,8)][::-1])

if len(sys.argv) != 7:
    print "Enter host number, number of MPs, selected MPs, number of rules, test number,topology number", sys.argv
else:
    #Save the host
    host = "h" + sys.argv[1][-1:]
    #Save the number of MPs
    numberOfMPs = sys.argv[2]
    #Choose maximum 1 MP to be pre selected
    preSelectedMP = sys.argv[3]
    #If the MP is 0, don't select any MP, otherwise set the selected number to be MP
    if '0' == preSelectedMP:
        preSelectedMPsList = []
    else:
        preSelectedMPsList = [preSelectedMP]
    #If the number of rules is not specifically 3, make it 4
    numberOfRules = sys.argv[4]
    if '3' != numberOfRules:
        numberOfRules = '4'
    #Save the test number to save the results in desired directory
    testNumber = sys.argv[5]
    #Save the topology to save the results in the topology directory
    topologyNumber = sys.argv[6]
    #Save the interface
    interface = host + "-eth0"

    #pcap file name to save the packets
    fileName = "/home/ubuntu/MyProject/captures/Test"+ testNumber + "/topology"+ topologyNumber +"/"+ numberOfRules+ "Rules/" + numberOfMPs+ "MPs"+preSelectedMP+"MP"+"/probe"+ host+ ".cap"
    if not os.path.exists(os.path.dirname(fileName)):
        os.makedirs(os.path.dirname(fileName))
    system("sudo rm -rf "+fileName) #remove the file if exist
    #sniff the packets in libpcap format in the background into the file with given file name
    system("dumpcap -i "+interface+" -w "+fileName+" -P -q &")

    sleep(1) #for file to open
    measurementRound = 1 #initial packetID

    #send the packet that discover topology with given number of rules
    sendTopologyDiscoveryPacket(int(numberOfRules))

    #Wait for topology to update
    sleep(4);

    #Prepare the data that need to be added to the analyzing packet
    dataToAdd = ExtraLayers.createMPsData(numberOfMPs, preSelectedMPsList)

    #Send the message to the controller - it will builed the topology
    sendAnalyzePacket(dataToAdd)

    #wait for overlay network
    sleep(4);

    #Send the probe packets
    sendProbePackets(ExtraLayers.numberOfTests, ExtraLayers.intervalBetweenTests)
    sleep(1) #for data to arrive before closing file
    system("killall dumpcap")
