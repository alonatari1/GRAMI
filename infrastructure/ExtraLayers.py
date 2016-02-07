__author__ = 'ubuntu'
from scapy.all import *
from time import time

''' In this file I define constants for my tests and build packets with Scapy.'''

'''Constant for testing - To be used with my testing scripts.'''
delayConst = 10000 # Time before starting the test in microseconds..
numberOfTests = 200 # How many probe packets should be sent.
intervalBetweenTests = 1000 # Time between probe packets in microseconds.

''' Constants for packets - Used for identification in the controller, part of manual activation
    I am currently using but not part of GRAMI '''
topologyHostEtherMAC = "00:11:12:13:14:15" # Constant for mac of packets in my topology analyzer application.
topologyControllerEtherMAC = "00:11:12:13:15:15" # Constant for mac that order the controller to activate the topology application.
analyzeEtherMAC = "00:11:12:13:14:16" # Constant for mac that order the controller to analyze the network
testStarMAC = "00:11:33:44:55:66" # Constant for mac of specific test in star topology.

''' Constants for ether types and VLANs'''
''' Manual activation - no part of GRAMI '''
analyzeType = 0xa01 # MP to controller analyze the network packet type.
topologyHostType = 0xa04 # MP to controller start topology application packet type.
topologyControllerType = 0xa05 # Topology application packet type (sent from controller to discover the network topology).
typeForTestingTaggingAndDuplicationTime = 0x500 # Used for packet duplication times test.
typeInstallStarTopoFlowEntries = 0x501 # Used for packet duplication times test.

''' GRAMI related '''
dirForward = 0xa02 # Direction forward in the network. Equivalent to DirectionFlag = TRUE and SetIDFlag = TRUE.
inRTP = 0xb02 # During RTP traversal tag. Equivalent to DirectionFlag = TRUE and SetIDFlag = False.
dirReturnAndTag = 0xa03 # Direction return in the network with tagging in the first switch on the way back. Equivalent to DirectionFlag = FALSE and SetIDFlag = TRUE.
dirReturnNoTag = 0xb03 # Direction return in the network without tagging. Equivalent to DirectionFlag = FALSE and SetIDFlag = FALSE.

''' 3 flow entries case '''
dirBackwardsThreeFlowEntries = 0xc03 # In the 3 flow entries case there is only one return tag.

''' VLAN constants'''
NULL_ID = 0x07ff # VLAM that will be pushed to represent no ID.
VLAN_ID_ETHERTYPE_QINQ = 0x88a8 # Ethertype for QinQ VLAN protocol.
VLAN_ETHERTYPE = 0x8100 # Ethertype for normal VLAN.
solidFlag = 0x0800 # Masking for representing if link is solid or dashed.
RTPFlag = 0x0400 # Masking to identify if probe packet traversed an RTP or link.

''' End of constants for ether types '''

''' Fields related - Added timestamp for future support of time syncronized MPs, GRAMI doesn't use the timestamp.'''
# Define the size of each field.
timeStampSize = 8
measurementRoundSize = 2
directionForwardSize = 2
prevSwitchIDSize = 2
directionReturnSize = 2
lastSwitchIDSize = 2

#define the positions of all the interesting fields
timeStampPos = 0 - timeStampSize
measurementRoundPos = timeStampPos - measurementRoundSize
directionForwardPos = measurementRoundPos - directionForwardSize
prevSwitchIDPos = directionForwardPos - prevSwitchIDSize
directionReturnPos = prevSwitchIDPos - directionReturnSize
lastSwitchIDPos = directionReturnPos - lastSwitchIDSize

'''Constant for separators'''
MPDataSeperatorData = "::"
numberOfMPsSeperator = "-"
MPsSeperator = ","
topologyDataSeparator = "{"
topologySperator = "?"



def getID1(packet):
    """
    Get ID 1 (in 4 flow entries it first switch id or NULL ID in case of RTP, in 3 flow entries its last switch ID).
    :param packet: The packet to extract the data from.
    :return:
    """
    return struct.unpack('>h',str(packet)[lastSwitchIDPos:lastSwitchIDPos+lastSwitchIDSize])[0]


def getID2(packet):
    """
    Get ID2 (in 4 flow entries its last switch ID or RTP ID, in 3 flow entries its first switch ID)
    :param packet: The packet to extract the data from.
    :return:
    """
    return struct.unpack('>h',str(packet)[prevSwitchIDPos:prevSwitchIDPos+prevSwitchIDSize])[0]


def getPacketState(packet):
    """
    Get the state of the packet (in 4 flow entries its can be forward, return no tag return and tag or in RTP
    In 3 flow entries it is used only to identify forward probe packets).
    :param packet: The packet to extract the data from.
    :return:
    """
    return struct.unpack('>h',str(packet)[directionForwardPos:directionForwardPos+directionForwardSize])[0]


def getReturnState3FlowEntirs(packet):
    """
    Get the return state only for 3 flow entries, not in use for 4 flow entries.
    :param packet: The packet to extract the data from.
    :return:
    """
    return struct.unpack('>h',str(packet)[directionReturnPos:directionReturnPos+directionReturnSize])[0]


def getMeasurementRound(packet):
    """
    Get the measurement round from the packet payload.
    :param packet: The packet to extract the data from.
    :return:
    """
    return struct.unpack('>h',str(packet)[measurementRoundPos:measurementRoundPos + measurementRoundSize])[0]


def getTimeStamp(packet):
    """
    Get the timestamp from the packet payload.
    :param packet: The packet to extract the data from.
    :return:
    """
    return struct.unpack('>q',str(packet)[timeStampPos:timeStampPos + timeStampSize])[0]



class ProbePacketPayload(Packet):
    """
    Extra layer for additional information.
    """
    name = "ProbePacketPayload"
    fields_desc=[ ShortField("MeasurementRound",0),LongField("Timestamp",int(time()*1000000) )] #Add measurement round to the packet and timestamp.



class Vlan(Packet):

    name = "Vlan"

    # Add the packet IDS with NULL ID and direction forward.
    fields_desc=[ ShortField("ID2",NULL_ID),ShortField("QinQvalue",VLAN_ID_ETHERTYPE_QINQ),ShortField("ID1",NULL_ID),ShortField("packetStatus",dirForward) ]


def createMPsData(numberOfMPs, MPs):
    """
    Create data string that will we be added to the analyze packet and represent the number of MPs and the MPs.
    :param numberOfMPs: How many MPs to use.
    :param MPs: The MPs to use
    :return: data string wit the mentioned info.
    """
    ''''''
    return  MPDataSeperatorData + numberOfMPs + numberOfMPsSeperator+ MPsSeperator.join(MPs)


def getMPsInfoFromPacket(pkt):
    """
    Get how many MPs to use and specific MPs to use from packet
    :param pkt: The packet to extract the data from.
    :return: How many MPs to use and list of MPs to use
    """

    MPsInfo = pkt[1].split(MPDataSeperatorData)[1]
    numberOfMPs = int(MPsInfo.split(numberOfMPsSeperator)[0])
    MPsString = MPsInfo.split(numberOfMPsSeperator)[1]
    MPs = []

    #If the MPs is not an empty string get all the MPs and add them to the list
    if ('' != MPsString):
        for strMP in MPsString.split(MPsSeperator):
            MPs.append(int(strMP))

    return numberOfMPs, MPs

def createTopologyMessage(port, switchID):
    '''
    Create a message that save the source switch and port.
    :param port: source port
    :param switchID: source switch
    :return: the message as string
    '''
    data = topologyDataSeparator + switchID + topologySperator + port
    return str((Ether(type = topologyControllerType,src = topologyControllerEtherMAC)/Vlan()/Raw(load=data)))

def getToplogyData(pkt):
    '''
    Get the topology data from the packet (it will be the source port and source switch ID from where the packet was sent)
    :param pkt: the packet arrived
    :return: return the dest switch and port
    '''
    topologyInfo = pkt[1].split(topologyDataSeparator)[1]
    switchID = int(topologyInfo.split(topologySperator)[0])
    port = int(topologyInfo.split(topologySperator)[1])
    return switchID, port