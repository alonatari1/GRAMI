__author__ = 'ubuntu'

import ExtraLayers #For the information analysis
from os import system #for cmd commands
import sys
import os
import math


noResult = 0xffffffff #represents no result for this link
numOfResultsForAverageRTT = 10 #How many packets back to consider for avg RTT

''' This file is used by the Analyzer to update the information about the packets
 reference packets are the packet that leave the switch and its leaving time will be reference to return time
 The switches will contain the RTT to get to them in shortest path (solid links only)
 The links will contain the RTT to get to them and the RTT to this link only
 '''

#This function get a list off tuples and an index and return the average value
#of all the tuples[index[ in this list
def getAvgTupleListByIndex(list,index):
    sum = 0
    count = 0
    for temp in list:
        count += 1
        sum += temp[index]
    return float(sum)/count

#Class for initializing the reference packet with its attribute
class referencePacket(object):
    '''The interesting parameters for reference packet are
    timestamp- the time it left the host
    packetID- the id of the packet left because the id stays in the return packet
    and that way we can know to which packet we should refer'''
    def __init__ (self,packetID,timeStamp):
        self.packetID = packetID
        self.timeStamp = timeStamp

#Class that contain list of reference packets
class referencePackets(object):
    #Init by creating empty list of reference packets, and last ID received
    def __init__ (self):
        self.packets = []

    #return the timestamp of the reference packet with given packet id
    def getRefTimeStamp(self,packetID):
        for p in self.packets:
            if (packetID == p.packetID):
                return p.timeStamp
        return 0 #for the case of no such packetID

    #add packet to the reference packets
    def addReferencePacket(self,packet):
        for p in self.packets:
            if (p.packetID == packet.packetID): #if packet with this ID exist already - update the timestamp
                self.packets.remove(p) #if reference packet received with same packet id remove the old one

        self.packets.append(packet)

    #return all the reference packets ID's
    def getRefIDs(self):
        IDs = []
        for p in self.packets:
            IDs.append(p.packetID)
        return IDs

    #Return a list of the last ID's send for reference measurements
    def getLastRefIDsForAvgRTTCalc(self):
        IDs = []
        for p in self.packets[-numOfResultsForAverageRTT:]:
            IDs.append(p.packetID)
        return IDs

class switch(object):
    '''This class will contain the RTT information of a switch
    For every switch we will save the switch ID
    all the results as tuples of result and packetID
    the avg RTT'''
    def __init__(self,switchID):
        self.switchID = switchID
        self.avgRTT = 0 #initial avg RTT is 0
        self.resultsRTT = [] #empty list for results RTT tuples (tuple of RTT and packetID)

     #Return the RTT tuple for given packetID
    def getSwitchRTTForGivenPacketID(self,packetID):
        for res in self.resultsRTT:
            #if there is packet id that match
            if (packetID == res[0]):
                #return the RTT
                return res[1]
        #if not packet ID matched it means there is no result
        return noResult

    #Add result to the current full switches and calculate the new average
    def addResult(self,packetID,RTT):
        #If there is a packet ID with this result- remove it
        for res in self.resultsRTT:
            if packetID == res[0]:
                self.resultsRTT.remove(res)
        #Add tuple of packet and RTT result
        self.resultsRTT.append((packetID,RTT))
        #Calculate new avg
        self.avgRTT = getAvgTupleListByIndex(self.resultsRTT, 1)

    #Get the avg RTT for this switch for given packetIDs
    #If the list is only one item it will return the result
    def getAvgSwitchRTTForGivenPacketIDs(self,packetIDs):
        sum = 0 #sum of RTTs
        count = 0 #how many results exist
        #Go over all the results
        for res in self.resultsRTT:
            #If the packet id is in the packet id list, add it to calculations
            if res[0] in packetIDs:
                sum += res[1] # add the RTT
                count += 1 #How many packets are valid
        #If the switch wasn't reachable for any of these packetIDs return no Result
        if (0 == count):
            return noResult
        #else return the avg
        return sum/float(count)

class switches(object):
    '''This class will hold and update the RTTs to all switches in my network
    for switches instance we will save the list of switches in our network (every switch contain all its results)
    we will save the last packet ID result and the number of reachable switches for that result'''

    #Init the full paths in my network
    def __init__ (self):
        #save all full paths
        self.switches = []
        #Save the last link that was updated so we can analyze all the result
        self.lastUpdatedResultsPacketID = -1
        #save the number of reachable switches in last activation
        self.numberOfReachableSwitches = 0

    #First check if switch exist and add it to the switches if exist
    #Then update the number of reachable switches and last handle packetID
    #Finally add the result to the given switch
    def addResult(self,switchID,packetID,RTT,linkType):
        #Add the result to the switch as shortest path only if link was solid
        #There is a single way to reach every switch with solid lines and this is the shortest path
        # regarding the number of links
        if (0 == linkType):
            return
        found = 0 #save if switch exist in switches or not
        #search in all the switches if switch with given switch ID already exists
        #switchID is a unique identifier
        for tempSwitch in self.switches:
            #if exist, save it and declare it was found
            if(switchID == tempSwitch.switchID):
                found = 1
                currSwitch = tempSwitch

        #if the switch was not found, create new switch and add it to the list of switches
        if (0 == found):
            currSwitch = switch(switchID)
            self.switches.append(currSwitch)

        #If the packet ID is older It's not interesting now because we want to get the number of reachable switches
        #for the last packet sent, if we will send with enough time between measurements we won't get those kind of
        #packets (returned a packet with ID x when packet with ID y returned before whe x<y)

        #If the packetID is equal to the last one analyzed add a new reachable switch
        if (packetID == self.lastUpdatedResultsPacketID):
            self.numberOfReachableSwitches += 1

        #If the given packetID is new, set it as last received and set number of reachable switches so
        #far for last test to be 1
        if (packetID > self.lastUpdatedResultsPacketID):
            self.lastUpdatedResultsPacketID = packetID
            self.numberOfReachableSwitches = 1

        #add the result to the current switch
        currSwitch.addResult(packetID,RTT)

    #get the RTT of given switch for given packet ID
    def GetRTTForSpecificSwitchIDAndPacketID(self,switchID,packetID):
        #go over all the switches
        for s in self.switches:
            #only one switch has the current switch ID- find it
            if (switchID == s.switchID):
                #Get this switch result which contains its RTT for given packet ID (might be noResult)
                currRTT = (s.getSwitchRTTForGivenPacketID(packetID))
                return currRTT
        #if the switch does not exist return no result
        return noResult

    #Get list of interesting results for all the switches
    #Will return a list of tuples  switchID, avg for given packetIDs, total avg, last results
    def getResultsForAllSwitches(self,packetIDs):
        Results = []
        for s in self.switches:
            #get the avg RTT for packet IDs
            avgRTTForPacketIDs = s.getAvgSwitchRTTForGivenPacketIDs(packetIDs)
            #get the total avgRTT
            avgRTT = s.avgRTT
            #get last RTT
            lastRTT = (s.resultsRTT[-1])[1]
            Results.append((s.switchID,avgRTTForPacketIDs,avgRTT,lastRTT))
        return Results

class link(object):
    '''This class will represent a link by 2 switch ID's connected to it
    by specifying the first and last switch ID , in addition it will save all the RTT of the link and for the
    full path toward it and the average of all results'''

    #Init the parameter for every link
    def __init__(self,startSwitchID,endSwitchID):
        self.startSwitchID = startSwitchID
        self.endSwitchID = endSwitchID
        self.avgLinkRTT = 0 #initial avg RTT for a single link is 0
        self.resultsLinkRTT = [] #empty list for results RTT for the link only tuples (tuple of packetID, RTT)
        self.avgFullPathRTT = 0 #initial avg RTT for a full path is 0
        self.resultsFullPathRTT = [] #empty list for results RTT for full path tuples (tuple of packetID, RTT, linkType)

    #Return the result for link RTT for given packetID
    def getLinkRTTForGivenPacketID(self,packetID):
        for res in self.resultsLinkRTT:
            if (packetID == res[0]):
                return res[1]
        return noResult

    #Return the result for full path RTT for given packetID
    def getFullPathRTTForGivenPacketID(self,packetID):
        for res in self.resultsLinkRTT:
            if (packetID == res[0]):
                return res[1]
        return noResult

    #Add result to the current link and calculate the new average for full path RTT
    def addFullPathRTTResult(self,packetID,fullPathRTT,linkType):
        #If there is a packet ID with this result- remove it
        for res in self.resultsFullPathRTT:
            if packetID == res[0]:
                self.resultsFullPathRTT.remove(res)
        #Add tuple of packet ID, RTT and type result, the tuple contain links type because it
        #May change from one measurement to another
        self.resultsFullPathRTT.append((packetID, fullPathRTT,linkType))
        #Calculate new avg
        self.avgFullPathRTT = getAvgTupleListByIndex(self.resultsFullPathRTT, 1)

    #Add result to the current link and calculate the new average for full normal RTT
    def addLinkRTTResult(self,packetID,linkRTT):
        #If there is a packet ID with this result- remove it
        for res in self.resultsLinkRTT:
            if packetID == res[0]:
                self.resultsLinkRTT.remove(res)

        #If it is no result still had to remove prev result if such existed, but no need to add it again
        if (noResult == linkRTT):
            return
        #Add tuple of packet ID, RTT and type result, the tuple contain links type because it
        #May change from one measurement to another
        self.resultsLinkRTT.append((packetID, linkRTT))
        #Calculate new avg
        self.avgLinkRTT = getAvgTupleListByIndex(self.resultsLinkRTT, 1)


    #Get the avg RTTs (links and full path) for this link for given packetIDs
    #If the list is only one item it will return the result
    def getAvgLinkRTTsForGivenPacketIDs(self,packetIDs):
        RTTs = [noResult,noResult] #list of list rtt and fullPathRTT
        sumLink = 0 #sum of RTTs
        countLink = 0 #how many results exist
        sumFullPath = 0 # sum of full paths RTT
        countFullPath = 0 # how many result for full path exist
        #Go over all the results
        for res in self.resultsLinkRTT:
            #If the packet id is in the packet id list, add it to calculations
            if res[0] in packetIDs:
                if (res != noResult):#make sure the result is a valid result and not an empty one
                    sumLink += res[1] # add the RTT
                    countLink += 1 #How many packets are valid

        for res in self.resultsFullPathRTT:
            #If the packet id is in the packet id list, add it to calculations
            if res[0] in packetIDs:
                if (res != noResult):#make sure the result is a valid result and not an empty one
                    sumFullPath += res[1] # add the RTT
                    countFullPath += 1 #How many packets are valid
        #If the switch was at least once for these packetIDs calc the results,otherwise there is no result
        if (0 != countLink):
            RTTs[0] =  sumLink/float(countLink)
        #If the switch was at least once for these packetIDs calc the results,otherwise there is no result
        if (0 != countFullPath):
            RTTs[1] =  sumFullPath/float(countFullPath)
        #ret the list
        return RTTs

class links(object):
    '''This class will hold and update the RTTs to all links in my network'''

    #Init the full paths in my network
    def __init__ (self):
        #save the reachable links
        self.reachableLinks = []
        #save the unreachable links
        self.unreachableLinks = []
        #save all full paths
        self.links = []
        #Save the last link that was updated so we can analyze all the result
        self.lastUpdatedResultsPacketID = -1

    #Must get the switches to get the fathers and sons RTT
    #First check if link exist and create one and add it to the links if not
    #Then update the number of reachable links and last handle packetID
    #Eventually update the result according to the father link, and update the result to the
    #son links if they arrived before the son link (will create negative RTT but might happen )
    def addResult(self,startSwitchID,endSwitchID,packetID,RTT,linkType,switches):
        found = 0 #save if link exist in links or not
        #search in all the links if switch with given link ID already exists
        for tempLink in self.links:
            #if exist, save it and declare it was found
            if((startSwitchID == tempLink.startSwitchID) and (endSwitchID == tempLink.endSwitchID)):
                found = 1
                currLink = tempLink

        #if the link was not found, create new link and add it to the list of links and the list of unreachable ones
        if (0 == found):
            currLink = link(startSwitchID,endSwitchID)
            self.links.append(currLink)
            self.unreachableLinks.append(currLink)

        #If the packet ID is older It's not interesting now because we want to get the number of reachable links
        #for the last packet sent, if we will send with enough time between measurements we won't get those kind of
        #packets (returned a packet with ID x when packet with ID y returned before whe x<y)

        #If the packetID is equal to the last one analyzed add a new reachable link and remove it from unreachable
        if (packetID == self.lastUpdatedResultsPacketID):
            self.reachableLinks.append(currLink)
            if (currLink in self.unreachableLinks):
                self.unreachableLinks.remove(currLink)

        #If the given packetID is new, set it as last received and set list of reachable and unreachable links
        if (packetID > self.lastUpdatedResultsPacketID):
            self.lastUpdatedResultsPacketID = packetID
            self.unreachableLinks = []
            self.unreachableLinks += self.links
            self.unreachableLinks.remove(currLink)
            self.reachableLinks = [currLink]


        #Add the full path result to the link (the current RTT is full paths result)
        currLink.addFullPathRTTResult(packetID,RTT,linkType)

        #if the father link is dummy it means it is the first link and the RTT is
        # the current RTT and there is nothing to subtract
        if (ExtraLayers.NULL_ID == startSwitchID):
            currLink.addLinkRTTResult(packetID,RTT)
        else:
            ### Handle the current link RTT by calculating with father result ###
            #the father switch RTT is only for solid links
            #this could be done without the switches by checking rtt of full paths for
            #links that end when current link starts and that the link is solid. but
            #this solution is easirt to understand
            fatherRTT = switches.GetRTTForSpecificSwitchIDAndPacketID(startSwitchID, packetID)

            #if no result it means that for that packetID the father result didn't arrive so cannot calculate links RTT
            if (noResult != fatherRTT):
                #add the result to the current link
                currLink.addLinkRTTResult(packetID, RTT - fatherRTT)
            else:
                #If had no result we dont want to add new one,
                #calling this function with no Result will cause remove of previous if exist
                currLink.addLinkRTTResult(packetID ,noResult)

        ###Handle sons links that might not have current link as a father to update link result###
        #if this is a solid link, we can try and update the link RTT to its sons if arrived or handled before..
        if (1 == linkType):
            for sonLink in self.links:
                #Update the result only if end of this link is the start of the other, and the link has
                #no result which means has to be updated
                if((currLink.endSwitchID == sonLink.startSwitchID) and (noResult == sonLink.getLinkRTTForGivenPacketID(packetID))):
                    #get its full path RTT
                    sonFullPathRTT = tempLink.getFullPathRTTForGivenPacketID(packetID)
                    #Set the RTT to be the full path minus the father (current link) RTT
                    tempLink.addLinkRTTResult(packetID, sonFullPathRTT - RTT)

    #Get list of interesting results for all the links
    #Will return a list of tuples:
    #Start switch ID, End switch ID , link type,
    #avg full RTT for given packetIDs, total full RTT avg, last results for full RTT,
    #avg link RTT for given packetIDs, total link RTT avg , last results for link RTT
    def getResultsForAllLinks(self,packetIDs):
        Results = []
        for l in self.links:
            #get the avg RTTs for packet IDs
            avgLinkRTTForPacketIDs,avgFullPathRTTForPacketIDs = l.getAvgLinkRTTsForGivenPacketIDs(packetIDs)
            #get the total avgRTTs
            avgLinkRTT = l.avgLinkRTT
            avgFullPathRTT = l.avgFullPathRTT
            #get last RTT
            lastLinkRTT = (l.resultsLinkRTT[-1])[1]
            lastFullPathRTT = (l.resultsFullPathRTT[-1])[1]
            #get the last link type
            lastLinkType = (l.resultsFullPathRTT[-1])[2]
            Results.append((l.startSwitchID,l.endSwitchID,lastLinkType,avgFullPathRTTForPacketIDs,avgFullPathRTT
                            ,lastFullPathRTT,avgLinkRTTForPacketIDs,avgLinkRTT, lastLinkRTT))
        return Results

    def printAllReachableAndUnreachableLinks(self):
        unreachableStr = "Unreacable links: "
        for l in self.unreachableLinks:
            unreachableStr += str(l.startSwitchID)
            unreachableStr += "<->"
            unreachableStr += str(l.endSwitchID)
            unreachableStr += " "
        reachableStr = "reachble links: "
        for l in self.reachableLinks:
            reachableStr += str(l.startSwitchID)
            reachableStr += "<->"
            reachableStr += str(l.endSwitchID)
            reachableStr += " "
        print unreachableStr
        print reachableStr




#handling all the packets sent and received
class myPacketHandler(object):
    def __init__ (self):
        self.referencePackets = referencePackets() #create the reference packet list
        self.links = links()
        self.switches = switches()

    #handle the packets by adding it to the list of packets
    def handlePacket(self,packet,sec,uSec):
        directionForward = ExtraLayers.getPacketState(packet) #get the direction forward
        packetID = ExtraLayers.getMeasurementRound(packet) #get the packet id
        directionReturn = ExtraLayers.getReturnState3FlowEntirs(packet) #get the direction return
        timeStamp = sec * 1000000 + uSec #calculate the timestamp in uSec
        #if this is a 4 rules case, in the "direction forward" location we will have the dirFirstBackward type, which means it is return packet
        #if this is a 3 rules case, in the "direction return" location we will have the direction backwards three rules tag
        if (ExtraLayers.dirReturnAndTag == directionForward or ( ExtraLayers.dirBackwardsThreeFlowEntries == directionReturn)): #if directed backwards it is a return packet
            #Get the RTT (time from packet sent to packet returned)
            #Because I am working in vm environment, I took the timestamp from the file, in normal environment the results will be extracted from the packet
            #The addition is because if we have delay of 10ms mininet wont actually send the packet in those 10 ms, therefore, need to add the time by ourselves
            RTT = timeStamp - self.referencePackets.getRefTimeStamp(packetID) + ExtraLayers.delayConst

            #If we are working with 3 rules, or with 4 rules, the tagging of the first and last switch ID is exactly the opposite, therefore need
            #to be handled differently. The case of the 3 or 4 tags can be identified according to the direction backwards tagging
            if (ExtraLayers.dirBackwardsThreeFlowEntries == directionReturn):
                #get the info about the switches ids that this packet represent
                prevSwitchID = ExtraLayers.getID2(packet)
                lastSwitchID = ExtraLayers.getID1(packet)

            else:
                 #get the info about the switches ids that this packet represent
                lastSwitchID = ExtraLayers.getID2(packet)
                prevSwitchID = ExtraLayers.getID1(packet)


            #get if the packer returned from solid link or dashed one
            if (ExtraLayers.solidFlag == (lastSwitchID & ExtraLayers.solidFlag)):
                linkType = 1
            else:
                linkType = 0

            #remove the solid flag
            lastSwitchID = (lastSwitchID & (0xffff- ExtraLayers.solidFlag))


            #Add the result to the switches
            self.switches.addResult(lastSwitchID,packetID,RTT,linkType)

            #It does not matter if it is a dashed link or a solid one, we need to add the
            #result to the link
            self.links.addResult(prevSwitchID,lastSwitchID,packetID,RTT,linkType,self.switches)
        #make sure it is not a return packet and check if it is forward packet
        else:
            #Both in 3 or 4 rules, when the packet leaves the switch has in the direction forward position, tagging of direction forward
            if (ExtraLayers.dirForward == directionForward):#if directed forward, it is a reference packet
                self.referencePackets.addReferencePacket(referencePacket(packetID,timeStamp))

    #print all the information on the reference return packets
    def printAllInfo(self):
        relevantPacketIDs = self.referencePackets.getLastRefIDsForAvgRTTCalc()
        switchResults = self.switches.getResultsForAllSwitches(relevantPacketIDs)
        linkResults = self.links.getResultsForAllLinks(relevantPacketIDs)
        for res in switchResults:
            print "switch: " , res[0], " had avg last" , numOfResultsForAverageRTT, "RTT:", res[1], \
            " tot avg RTT:" , res[2], "and last RTT:" , res[3]

        self.links.printAllReachableAndUnreachableLinks()

        for res in linkResults:
            print "link:" , res[0], "-" , res[1] , "had last type:", res[2],\
            "avg last" , numOfResultsForAverageRTT, "link RTT :", res[6], \
            "tot avg link RTT:" , res[7], "last link RTT:" , res[8],\
            "avg last" , numOfResultsForAverageRTT, " full path  RTT:", res[3], " tot avg full path RTT:" , res[4], \
            " and last full path RTT:" , res[5]
        print "\r\n"

    #Save both sorted and non sorted version
    def writeSortedAndNonSortedResults(self, results, fileName, filePath):

        outFileName = filePath + "/NonSorted" + fileName
        if not os.path.exists(os.path.dirname(outFileName)):
            os.makedirs(os.path.dirname(outFileName))
        system("sudo rm -rf "+ outFileName) #remove the out file if exist
        #Create output file
        outFile = open(outFileName, "w")
        #Print all the results
        for RTT in results:
            outFile.write(str(RTT[1])+'\n')
        #close the file
        outFile.close()

        outFileName = filePath + "/Sorted" + fileName
        if not os.path.exists(os.path.dirname(outFileName)):
            os.makedirs(os.path.dirname(outFileName))
        system("sudo rm -rf "+ outFileName) #remove the out file if exist
        #Create output file
        outFile = open(outFileName, "w")
        #Print all the results
        RTTresults = []
        for result in results:
            RTTresults.append(result[1])
        sortedRTTresults = sorted(RTTresults)
        lenResults = len(sortedRTTresults)
        cutSortedRTTResults = sortedRTTresults[int(round(lenResults*0.05)):int(round(lenResults*0.95))]
        for RTT in cutSortedRTTResults:
            outFile.write(str(RTT)+'\n')


        #close the file
        outFile.close()

    def myAvg(self, list):
        RTTresults = []
        for result in list:
            RTTresults.append(result[1])
        sortedRTTresults = sorted(RTTresults)
        lenResults = len(sortedRTTresults)
        cutSortedRTTResults = sortedRTTresults[int(round(lenResults*0.05)):int(round(lenResults*0.95))]
        avg = float(sum(cutSortedRTTResults))/len(cutSortedRTTResults)
        return avg

    def myStdev(self, list):
        RTTresults = []
        for result in list:
            RTTresults.append(result[1])
        sortedRTTresults = sorted(RTTresults)
        lenResults = len(sortedRTTresults)
        cutSortedRTTResults = sortedRTTresults[int(round(lenResults*0.05)):int(round(lenResults*0.95))]
        avg = float(sum(cutSortedRTTResults))/len(cutSortedRTTResults)
        dev = []
        for x in cutSortedRTTResults:
            dev.append(x-avg)
        sqr = []
        for x in dev:
            sqr.append(x*x)
        std = math.sqrt(sum(sqr)/(len(sqr)))
        return std

    #Get all the results, and save all the data in the relevant file and directory, for evey link,
    #For evey switch, for all the links and for links by depth
    def saveInfoInFiles(self, testNumber, topologyNumber, numberOfRules, host , numberOfMPs,preSelectedMP):
        #Save the file path for specific test,topo, number of MPs and first MP
        filePath = "/home/ubuntu/Results/Test"+ testNumber + "/topology"+ topologyNumber+ "/"+ numberOfRules+ "Rules/" + numberOfMPs+ "MPs" + preSelectedMP+"MP"
        for s in self.switches.switches:
            #get all the results for the switch
            results = s.resultsRTT
            fileName = "/probe"+ host + "toS" +str(s.switchID) +"with" + numberOfRules+ "rules.txt"

            self.writeSortedAndNonSortedResults(results, fileName, filePath)

        #Save enough space for multyple rules
        resultsByDepth = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
        stdByDepth = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
        AllStd = []

        #Create the info for all the links and save them by depth (depth is according to assumption that average
        #per link is a little above 20000)
        for l in self.links.links:
            strEndSwitch = "S" + str(l.endSwitchID)
            if (ExtraLayers.NULL_ID == l.startSwitchID):
                strStartSwitch = host
            else:
                strStartSwitch = "S" + str(l.startSwitchID)

            #get all the results for the switch
            results = l.resultsLinkRTT

            #print all the average results
            print "From S" + str(l.startSwitchID) + " to S" + str(l.endSwitchID) + " is " + str(self.myAvg(results))

            #calculate depth index
            depthIndex = 0;
            avgRtt = l.avgFullPathRTT - 20000
            while (avgRtt >0 ):
                depthIndex = depthIndex + 1
                avgRtt = avgRtt - 20000

            stdByDepth[depthIndex-1].append(self.myStdev(results))
            #Save all the results
            for RTT in results:
                resultsByDepth[depthIndex-1].append(RTT)


            fileName = "/probe"+ strStartSwitch + "to" + strEndSwitch +"with" + numberOfRules+ "rules.txt"
            self.writeSortedAndNonSortedResults(results, fileName, filePath)

        #Get the maximal depth
        maxDepth = 0
        while len(resultsByDepth[maxDepth])>0:
            maxDepth +=1;

        #Save info on std by depth
        outFileName = filePath + "/stdSortedByDepth.txt"
        if not os.path.exists(os.path.dirname(outFileName)):
            os.makedirs(os.path.dirname(outFileName))
        system("sudo rm -rf "+ outFileName) #remove the out file if exist
        #Create output file
        outFile = open(outFileName, "w")
        #Print all the results
        for depth in xrange(maxDepth):
            for res in stdByDepth[depth]:
                outFile.write(str(res)+'\n')
        #close the file
        outFile.close()


        #Save info by depth
        for depth in xrange(maxDepth):
            fileName = "/probeAllLinksFor"+host +"WithDepth"+str((depth+1)) +"And" + numberOfRules+ "rules.txt"
            self.writeSortedAndNonSortedResults(resultsByDepth[depth], fileName, filePath)
            print "The avg stdev for len:", (depth+1) ,  "is:" , float(sum(stdByDepth[depth])/len(stdByDepth[depth])), "with " , len(stdByDepth[depth]), "links"

        #Save the info for all the links in the network
        allLinksResults = []
        for l in self.links.links:
            #get all the results for the switch
            results = l.resultsLinkRTT
            AllStd.append(self.myStdev(results))

            #Print all the results
            for RTT in results:
                allLinksResults.append(RTT)


        fileName = "/probeAllLinksFor"+host +"With" + numberOfRules+ "rules.txt"
        self.writeSortedAndNonSortedResults(allLinksResults, fileName, filePath)
        print "The total stdev is:" , float(sum(AllStd)/len(AllStd)), "with " , len(AllStd), "links"
