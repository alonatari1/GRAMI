__author__ = 'ubuntu'

from scapy.all import * #for scapy
from os import system #for cmd commands
from time import sleep #for waiting between commands
import ExtraLayers #for the extra information added over my packets
import myPackets #for handling my packets
import sys
import time

#The only interface for pure switching is h1 and it works in topoPaper2 only
interface = "h1-eth0"

#Save the last ID of ping was sent and time it was sent
lastIDSent = -1
lastIDRTTReference = 0

#The file name where the results are stored
pcapFileName ="/home/ubuntu/MyProject/captures/Test1/topology2pure/h1Len"+sys.argv[1]+".cap"

time.sleep(1);
#set a file reader
a = PcapReader(pcapFileName)
pcapFile = a.f

#Save the RTT results
results = []

#Set a file reader
a = PcapReader(pcapFileName)
pcapFile = a.f
currPos = pcapFile.tell() #save current position
hdr = pcapFile.read(16) #read the header
count = 0
lastPureTime = 0
#while we keep getting messages
while ((lastPureTime == 0) or ((time.time() - lastPureTime) < 2)):
    #If the header is not ready yet, wait for a while and keep on going
    if (len(hdr) < 16):
        sleep(0.1)
        pcapFile.seek(currPos)

    elif (len(hdr) == 16):
        sec,uSec,capLen,wireLen = struct.unpack(a.endian+"IIII", hdr) #parse the header
        packet = pcapFile.read(capLen)
        #Analyze only packets with capLen equal to expected pureSwitching sent/ response
        if (32 == capLen):
            lastPureTime = time.time()
            packetID = ExtraLayers.getMeasurementRound(packet) #get the packet id
            count+=1
            if (packetID != lastIDSent): #If this is a packet sent, update reference time and last sent time
                lastIDRTTReference = sec * 1000000 + uSec
                lastIDSent = packetID
            else: #If packet received save the RTT
                RTT =  sec * 1000000 + uSec - lastIDRTTReference + ExtraLayers.delayConst
                results.append(RTT)

    currPos = pcapFile.tell() #save the current position
    hdr = pcapFile.read(16) # read the header


#Create the results, both sorted and non sorted.
filePath = "/home/ubuntu/Results/Test1/topology2pure"
outFileName = filePath + "/NonSorted" + "/Len"+sys.argv[1]+".txt"
if not os.path.exists(os.path.dirname(outFileName)):
    os.makedirs(os.path.dirname(outFileName))
system("sudo rm -rf "+ outFileName) #remove the out file if exist
#Create output file
outFile = open(outFileName, "w")
#Print all the results
for RTT in results:
    outFile.write(str(RTT)+'\n')
#close the file
outFile.close()

outFileName = filePath + "/Sorted" + "/Len"+sys.argv[1]+".txt"
if not os.path.exists(os.path.dirname(outFileName)):
    os.makedirs(os.path.dirname(outFileName))
system("sudo rm -rf "+ outFileName) #remove the out file if exist
#Create output file
outFile = open(outFileName, "w")

#Get all the results
RTTresults = []
for result in results:
    RTTresults.append(result)
sortedRTTresults = sorted(RTTresults)
lenResults = len(sortedRTTresults)
print "number of result" , lenResults
cutSortedRTTResults = sortedRTTresults[int(round(lenResults*0.05)):int(round(lenResults*0.95))]
for RTT in cutSortedRTTResults:
    outFile.write(str(RTT)+'\n')
#close the file
outFile.close()
