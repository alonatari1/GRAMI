__author__ = 'ubuntu'

from scapy.all import * #for scapy
from os import system #for cmd commands
from time import sleep #for waiting between commands
import ExtraLayers #for the extra information added over my packets
import myPackets #for handling my packets
import sys
import time

#Preapare the data
if len(sys.argv) != 7:
    print "Enter host number, number of roots, selected roots, number of rules, test number,topology number", sys.argv
else:
    #Save the host
    host = "h" + sys.argv[1][-1:]
    #Save the number of roots
    numberOfRoots = sys.argv[2]
    #Choose maximum 1 root to be pre selected
    preSelectedRoot = sys.argv[3]
    #If the root is 0, don't select any root, otherwise set the selected number to be root
    if '0' == preSelectedRoot:
        preSelectedRootsList = []
    else:
        preSelectedRootsList = [preSelectedRoot]
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

#Save the last ID of ping was sent and time it was sent
lastIDSent = -1
lastIDRTTReference = 0

#Save the pcap file Name
pcapFileName = "/home/ubuntu/MyProject/captures/Test"+ testNumber + "/topology"+ topologyNumber +"/"+ numberOfRules+ "Rules/" + numberOfRoots+ "Roots"+preSelectedRoot+"root"+"/probe"+ host+ ".cap"

time.sleep(1);

#create packet lists
sniffedPackets = myPackets.myPacketHandler()

#set a file reader
a = PcapReader(pcapFileName)
pcapFile = a.f
currPos = pcapFile.tell() #save current position
hdr = pcapFile.read(16) #read the header
count = 0
lastProbeTime = 0
while ((lastProbeTime == 0) or ((time.time() - lastProbeTime) < 2)):
    if (len(hdr) < 16):
        sleep(0.1)
        pcapFile.seek(currPos)

    elif (len(hdr) == 16):
        sec,uSec,capLen,wireLen = struct.unpack(a.endian+"IIII", hdr) #parse the header
        #print "wirelen" , wireLen, "capLen", capLen, "sec", sec, "uSec", uSec
        packet = pcapFile.read(capLen)
        #Analyze only packets with capLen equal to expected ping sent/ response
        if (32 == capLen):
            lastProbeTime = time.time()
            sniffedPackets.handlePacket(packet,sec,uSec) #handle the packet by adding it to reference packet list or return packet list
    currPos = pcapFile.tell() #save the current position
    hdr = pcapFile.read(16) # read the header

sniffedPackets.saveInfoInFiles(testNumber,topologyNumber,numberOfRules,host,numberOfRoots,preSelectedRoot)
print "done"
