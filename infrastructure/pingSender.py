from scapy.all import * #for scapy
from time import sleep #for waiting between commands
import thread
import ExtraLayers #for the extra information added over my packets
import sys
from os import  system

interface = "h1-eth0"

if len(sys.argv) != 2:
    print "Enter  dest host number", sys.argv
else:
    #temporary file to save the info
    fileName = "/home/ubuntu/MyProject/captures/Test1/topology0ping/" +"h" + sys.argv[1] + ".cap"
    if not os.path.exists(os.path.dirname(fileName)):
        os.makedirs(os.path.dirname(fileName))
    system("sudo rm -rf "+fileName) #remove the file if exist
    #sniff the packets in libpcap format in the background into the file with given file name
    system("dumpcap -i "+interface+" -w "+fileName+" -P -q &")



#Send the packet that should be distributed
def sendAndPrintPacket(numberOfPackets, interval):
    global measurementRound
    global ip
    count = 0
    #Send given number of packets
    while (count < numberOfPackets):
        #construct the packet with my extra layer
        packet = Ether()/IP(dst="10.0.0." + str(ip), ttl=20)/ICMP()/ExtraLayers.ProbePacketPayload(ID = packetId)
        print "ID" , packetId
        sendp(packet) #send the packet
        sleep((float)(interval)/1000) #Sleep for given amount of times
        packetId += 1 #increase the packet id
        count += 1

if len(sys.argv) != 2:
    ip = 2 #default ip is h2
else:
    ip = sys.argv[1]

#For file to open
sleep(1)
measurementRound = 1 #initial packetID
sendAndPrintPacket(ExtraLayers.numberOfTests, ExtraLayers.intervalBetweenTests)
#For all the data to arrive
sleep(1)
system("killall dumpcap")


