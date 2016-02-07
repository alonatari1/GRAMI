__author__ = 'ubuntu'

from scapy.all import * #for scapy
from os import system #for cmd commands
from time import sleep #for waiting between commands
import ExtraLayers #for the extra information added over my packets
import myPackets #for handling my packets
import sys
import time

#Set the interface (if given set it to be the given, if not the default is h1)
interface = "h1-eth0"
#Save the last ID of ping was sent and time it was sent
lastIDSent = -1
lastIDRTTReference = 0

if len(sys.argv) != 2:
    print "Enter  dest host number", sys.argv
else:
    #temporary file to save the info
    fileName = "/home/ubuntu/MyProject/captures/Test1/topology0ping/" +"h" + sys.argv[1] + ".cap"

    outFileName = "/home/ubuntu/Results/Test1/topology0ping" +"/h"+sys.argv[1]+".txt"

    if not os.path.exists(os.path.dirname(outFileName)):
        os.makedirs(os.path.dirname(outFileName))
    system("sudo rm -rf "+ outFileName) #remove the out file if exist

    #Create output file
    outFile = open(outFileName, "w")

    time.sleep(1);
    #set a file reader
    a = PcapReader(fileName)
    pcapFile = a.f

    #####I probably have error in running here. But  don't think I will run this file again.
    results = []

    currPos = pcapFile.tell() #save current position
    hdr = pcapFile.read(16) #read the header
    count = 0
    lastPingTime = 0
    while ((lastPingTime == 0) or ((time.time() - lastPingTime) < 2)):
        if (len(hdr) < 16):
            sleep(0.1)
            pcapFile.seek(currPos)

        elif (len(hdr) == 16):
            sec,uSec,capLen,wireLen = struct.unpack(a.endian+"IIII", hdr) #parse the header
            #print "wirelen" , wireLen, "capLen", capLen, "sec", sec, "uSec", uSec
            packet = pcapFile.read(capLen)
            #Analyze only packets with capLen equal to expected ping sent/ response
            if (52 == capLen):
                lastPingTime = time.time()
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

    #Get all the results, both sorted and non-sorted
    filePath = "/home/ubuntu/Results/Test1/topology0ping"
    outFileName = filePath + "/NonSorted" + "/h"+sys.argv[1]+".txt"
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

    outFileName = filePath + "/Sorted" + "/h"+sys.argv[1]+".txt"
    if not os.path.exists(os.path.dirname(outFileName)):
        os.makedirs(os.path.dirname(outFileName))
    system("sudo rm -rf "+ outFileName) #remove the out file if exist
    #Create output file
    outFile = open(outFileName, "w")
    #Print all the results
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
