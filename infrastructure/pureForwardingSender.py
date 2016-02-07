from scapy.all import * #for scapy
from time import sleep #for waiting between commands
import thread
import ExtraLayers #for the extra information added over my packets
import sys
from os import  system
from uuid import  getnode as get_mac #getting MAC

#The pure forwarding is tested from h1 one in paperTopo2
interface = "h1-eth0"

#pcapfile to save the info
fileName = "/home/ubuntu/MyProject/captures/Test1/topology2pure/h1Len"+sys.argv[1]+".cap"
if not os.path.exists(os.path.dirname(fileName)):
    os.makedirs(os.path.dirname(fileName))
system("sudo rm -rf "+fileName) #remove the file if exist
#sniff the packets in libpcap format in the background into the file with given file name
system("dumpcap -i "+interface+" -w "+fileName+" -P -q &")

#Get the sender mac with given
def getSenderMac():
    return ':'.join(['{:02x}'.format((get_mac() >> i) & 0xff) for i in range(0,8*6,8)][::-1])

def sendPureForwardingPacket():
    '''Send a message that will install the pure forwarding rules on topoPaper2'''
    packet = Ether(src = ExtraLayers.pureForwardingMac)/ExtraLayers.Vlan()/ExtraLayers.ProbePacketPayload(ID = 0)
    sendp(packet) #send the packet
    packet.show() #print the packet for debugging

#Send the pure switching packet, different ether types for different lengths of paths
def sendPurePackets(numberOfPackets, interval, etherType):
    global measurementRound
    count = 0
    #Send given number of packets
    while (count < numberOfPackets):
        #construct the packet with my extra layer
        packet = Ether(type = etherType ,src = getSenderMac())/ExtraLayers.Vlan()/ExtraLayers.ProbePacketPayload(ID = packetId)
        print packetId
        sendp(packet) #send the packet
        sleep((float)(interval)/1000) #Sleep for given amount of times
        packetId += 1 #increase the packet id
        count += 1

#Sleep second to wait for the file to open
sleep(1)
measurementRound = 1 #initial packetID
#Send the packet that will install the rules
sendPureForwardingPacket()
#Sleep for 10 seconds until the rules will be installed
sleep(10)
#Send the pure switching packets
sendPurePackets(ExtraLayers.numberOfTests, ExtraLayers.intervalBetweenTests, ExtraLayers.PureForwardingEtherTypeBase + int(sys.argv[1]) )

#For all the data to arrive
sleep(1)
system("killall dumpcap")


