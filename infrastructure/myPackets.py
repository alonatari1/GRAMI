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

#simple global func to calculte the mean of an array
def mean(array):
    return sum(array) / len(array) 
 
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
        
#handling all the packets sent and received
class myPacketHandler(object):
    def __init__ (self):
        self.referencePackets = referencePackets() #create the reference packet list
        self.switches = {}
        self.links = {}
        self.rtps = {}
        self.addRTP( 1, [1, 2, 3, 1])
        self.unvalidMeasurementRoundIDs = []
        
    #handle the packets by adding it to the list of packets
    def handlePacket(self,packet,sec,uSec):
        directionForward = ExtraLayers.getPacketState(packet) # get the direction forward
        
        #ignore unvalid measurment rounds
        packetID = ExtraLayers.getMeasurementRound(packet) # get the packet id
        if packetID in self.unvalidMeasurementRoundIDs:
            return
            
        timeStamp = float(sec * 1000000 + uSec)/1000 # calculate the timestamp in uSec
        
        if (directionForward == ExtraLayers.DistributeMAC):#if directed forward, it is a reference packet
            self.referencePackets.addReferencePacket(referencePacket(packetID,timeStamp))
            return
        
        # check if mac of packet is relecant to GRAMI
        if directionForward != ExtraLayers.ReturnAndTagMAC and directionForward != ExtraLayers.ReturnNoTagMAC: #if not directed backwards it is unrelevant packet
            return
        
        #Get the RTT (time from packet sent to packet returned)
        RTT = timeStamp - self.referencePackets.getRefTimeStamp(packetID)

        # get the info about the switches ids that this packet represent
        lastSwitchID = ExtraLayers.getID2(packet)
        prevSwitchID = ExtraLayers.getID1(packet)
        
        validResult = True
        
        # if it is a RTP packet
        if lastSwitchID == ExtraLayers.NULL_ID and prevSwitchID != ExtraLayers.NULL_ID:
            validResult = self.addRTPResult(prevSwitchID, packetID, RTT)
        else:            
            #get if the packer returned from solid link or dashed one
            linkIsSolidType = (ExtraLayers.solidFlag == (lastSwitchID & ExtraLayers.solidFlag))
            
            #remove the solid flag
            lastSwitchID = (lastSwitchID & (0xffff- ExtraLayers.solidFlag))

            #Add the result to the switches
            self.addSwitchResult(lastSwitchID,packetID,RTT)
            #It does not matter if it is a dashed link or a solid one, we need to add the
            #result to the link
            validResult = self.addLinkResult(prevSwitchID,lastSwitchID,packetID,RTT,linkIsSolidType)
        
        # if the result is not valid, ignorethe rest of this measurment round
        if not validResult:
            self.unvalidMeasurementRoundIDs.append(packetID)
            for results in self.switches.values():
                if packetID in results:
                    del results[packetID]
            for linkResults in self.links.values():
                if packetID in linkResults['RTTs']:
                    del linkResults['RTTs'][packetID]
            for rtp in self.rtps.values():
                if packetID in rtp['results']:
                    del rtp['results'][packetID]

    #check if an RTT time is resonable
    def validResult(self, RTT):
        MIN_RTT_VALUE = 0.1
        
        return RTT > MIN_RTT_VALUE
    
    #add a switch rtt result
    def addSwitchResult(self, switchID, packetID, RTT):
        if switchID not in self.switches.keys():
            self.switches[switchID] = {}
        if packetID not in self.switches[switchID]:
            self.switches[switchID][packetID] = RTT
    
    #print switch rtt result
    def printSwitchResults(self):
        for switchID, switchResults in self.switches.iteritems():
            if not switchResults:
                continue
            print "Switch {0} - Last RTT {1} - Average RTT {2} - Total RTTs number {3}".format( switchID, 
                switchResults.values()[-1] ,mean(switchResults.values()), len(switchResults) )
    
    #print a link rtt result
    def printLinkResults(self):
        for link, linkResults in self.links.iteritems():
            if not linkResults['RTTs']:
                continue
            print "Link {0} - Solid: {1} - Last RTT {2} - Average RTT {3} - Total RTTs number {4}".format( link, linkResults['linkType'],
                linkResults['RTTs'].values()[-1] ,mean(linkResults['RTTs'].values()), len(linkResults['RTTs']) )
    
    #add a link rtt result
    def addLinkResult(self, prevSwitchID,lastSwitchID,packetID,RTT,linkType):
        #if it is the link between MP to the first switch
        if prevSwitchID == ExtraLayers.NULL_ID:
            linkRTT = RTT
        #calc the diffrence between the switch RTT to the link recieve time
        elif ( prevSwitchID in self.switches.keys() ) and ( packetID in self.switches[prevSwitchID].keys() ):
            linkRTT = RTT - self.switches[prevSwitchID][packetID]
        else:
            print "Error: Recieved RTT packet in the wrong order"
            return False
        
        #add the link to reuslt dict
        currentLink = (prevSwitchID, lastSwitchID)
        if currentLink not in self.links.keys():
            self.links[currentLink] = { 'linkType' : linkType, 'RTTs' : {} }    
        self.links[currentLink]['RTTs'][packetID] = linkRTT
        return self.validResult( self.links[currentLink]['RTTs'][packetID] )

    #add a RTP packet montioring to the dict
    def addRTP(self, RTPID, path):
        self.rtps[RTPID] = { 'path': path, 'results' : {} }
        
    def addRTPResult(self, RTPID, packetID, RTT):
        startSwitchID = self.rtps[RTPID]['path'][0]
        
        #Calc the RTP by sub the first switch RTT in RTP from the packet recieve time
        if ( startSwitchID in self.switches.keys() ) and ( packetID in self.switches[startSwitchID].keys() ):
            self.rtps[RTPID]['results'][packetID] = RTT - self.switches[startSwitchID][packetID]
            return self.validResult( self.rtps[RTPID]['results'][packetID] )
    
        print "Error: Recivevd RTP packet in the wrong order"
        return False

    #print all RTPs results
    def printRTPResults(self):
        for id, rtp in self.rtps.iteritems():
            if not rtp['results']:
                continue
            
            print "RTP ID {0} - Path {1} - Last RTP {2} - Average RTP {3} - Total RTPs number {4}".format( id, rtp['path'],
                rtp['results'].values()[-1] ,mean(rtp['results'].values()), len(rtp['results']) )
        
    #print all the information on the reference return packets
    def printAllInfo(self):
        os.system( "rm resultsGRAMI" )
        f=open( "resultsGRAMI", "a")
        print "*** Switches ***"
        self.printSwitchResults()
        print "*** Links ***"
        self.printLinkResults()
        print "*** RTPs ***"
        self.printRTPResults()
        for result in self.links[(2,3)]['RTTs'].values():
            f.write( "{0}\n".format(result) )
