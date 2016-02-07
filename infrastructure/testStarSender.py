__author__ = 'ubuntu'

from scapy.all import * #for scapy
from time import sleep #for waiting between commands
import thread
import ExtraLayers #for the extra information added over my packets
import sys
from os import system
from uuid import  getnode as get_mac #getting MAC

def sendInstallStarRules():
    '''Send a message that will install the star flow entries'''
    packet = Ether(src = ExtraLayers.testStarMAC)/ExtraLayers.Vlan()/ExtraLayers.ProbePacketPayload(ID = 0)
    sendp(packet) #send the packet

#Send the packet that should first send two copies to the next switches and then add tag and send to other switch
def sendTestStarPackets(numberOfPackets, interval):
    global measurementRound
    count = 0
    #Send given number of packets
    while (count < numberOfPackets):
        #construct the packet with my extra layer
        packet = Ether(type = ExtraLayers.typeForTestingTaggingAndDuplicationTime ,src = getSenderMac())/ExtraLayers.Vlan()/ExtraLayers.ProbePacketPayload(ID = packetId)
        print packetId
        sendp(packet) #send the packet
        sleep((float)(interval)/1000) #Sleep for given amount of times
        packetId += 1 #increase the packet id
        count += 1

#Get the sender mac with given
def getSenderMac():
    return ':'.join(['{:02x}'.format((get_mac() >> i) & 0xff) for i in range(0,8*6,8)][::-1])


#Save the host
host = "h1"

#Save the interface
interface = host + "-eth0"

#pcap file name to save the packets
fileName = "/home/ubuntu/MyProject/captures/TestTemp/"+ host+ ".cap"
if not os.path.exists(os.path.dirname(fileName)):
    os.makedirs(os.path.dirname(fileName))
system("sudo rm -rf "+fileName) #remove the file if exist

#sniff the packets in libpcap format in the background into the file with given file name
system("dumpcap -i "+interface+" -w "+fileName+" -P -q &")
measurementRound = 1

#Send the message to the controller - it will builed the topology
sendInstallStarRules()

#wait for overlay network
sleep(4);

#Send the probe packets
sendTestStarPackets(5, 3000)