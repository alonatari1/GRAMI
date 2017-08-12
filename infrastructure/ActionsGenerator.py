__author__ = 'ubuntu'

from ryu.ofproto import ofproto_v1_3_parser
import ExtraLayers #for our layers information

''' Constants '''
OF_IN_PORT = 0xfffffff8 # Input port constant (OpenFlow constant for version 1.1 and above).
vlanIDMasking  = 0x1000  # Masking that ryu requires for sending vlan


def retMaskedVlanID(vlanID):
    """
    Return vlan ID with masking of the value required by ryu
    :param vlanID:
    :return:
    """
    #convert to short and use the mask
    return ((vlanID & 0xffff)|vlanIDMasking)


class ActionsGenerator(object):
    """
    Action generator for creating the actions for the flow entries.
    """


    def __init__ (self, portInfoGraph, OverlayGraph, rtp_switch_to_start_points):
        """
        Initialize the action generator with information from 2 graphs. The first with ports information and the
        second with te overlay netork information.
        :param portInfoGraph:  Graph with ports information.
        :param OverlayGraph:  The overlay network graph.
        :return:
        """

        # Dictionary that maps between a witch and its distribution ports.
        self.switch_to_distribution_port = {}

        # Dictionary that maps between a witch and its parent port (The single ingess solid link is connected to that port).
        self.switch_to_parent_port = {}
        
        self.rtp_switch_to_start_points = rtp_switch_to_start_points
                
        # Graph with info about the ports, (the original graph that for every edge, we have also the source and dest port).
        self.portInfoGraph = portInfoGraph

        # The overlay graph contains the distribution switches and parent switches for every switch.
        self.OG = OverlayGraph
        
        #Save the distribution ports and parent port for every switch.
        self.initPorts()
        

    def initPorts(self):
        """ Given the overlay graph, that sets the distribution switches and parent switches of every switch in the network
        and the portInfoGraph that contain the mapping between connected switched to source and dest port, return for every
        switch it's distribution ports and parent port'
        :return:
        """
        
        # NOTE: this function can be written with better complexity or otherwise one might implement the overlay network
        # with port information and this function will be redundant.

        # Traverse all the nodes (switches) in the graph.
        for node in self.OG.graph.nodes():
            #print "node" , node , "parent switch " ,self.OG.parentSwitch[node], "dist" , self.OG.distributionSwitches[node]

            # Get the parent switch and distribution switches for current node.
            parentSwitch = self.OG.parentSwitch[node]
            distributionSwitches = self.OG.distributionSwitches[node]

            # Initialize the list of distribution ports of this node to be empty.
            self.switch_to_distribution_port[node] = []

            # Run on all the edges (links).
            for edge in self.portInfoGraph.edges(data = True):

                # Handle distribution ports
                # If the edge is from current node to distribution switch, add the source port to distribution ports of current node
                if ((edge[2]['src'] == node) and (edge[2]['dst'] in distributionSwitches)):
                    self.switch_to_distribution_port[node].append(edge[2]['srcPort'])
                # If the edge is from distribution switch to current switch, add the dest port to distribution ports of current node
                elif (edge[2]['dst'] == node) and (edge[2]['src'] in distributionSwitches):
                    self.switch_to_distribution_port[node].append(edge[2]['dstPort'])

                # Handle parent port
                # If the edge is from parent switch to current node, add the dest port to be parent port current node
                if ((edge[2]['dst'] == node) and (edge[2]['src'] == parentSwitch)):
                    self.switch_to_parent_port[node] = edge[2]['dstPort']
                # If the edge is from current node to parent switch, add the source port to be parent port current node
                elif ((edge[2]['src'] == node) and (edge[2]['dst'] == parentSwitch)):
                    self.switch_to_parent_port[node] = edge[2]['srcPort']
                    
                # If the node is the parent switch it means that it is MP and it is connected via port 1 (The MP is not a switch).
                if (node == parentSwitch):
                    self.switch_to_parent_port[node] = 4
             
             
    def getRTPForwardAction(self, outPort):
        '''
        Get the RTP foward rule
        :param outPort: out port of current switch.
        :return: RTP Forward flow entry to be installed
        '''
        return [ofproto_v1_3_parser.OFPActionOutput(outPort)]
    
    def getRTPReturnActions(self, switchID, inPort):
        '''
        Get the return rtp packet to the given switch.
        :param switchID: ID of current switch.
        :param switchID: in port of switch.
        :return: distribution flow entries to be installed
        '''
        # set as reutrn packet
        actions = []
        actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_src = ExtraLayers.ReturnNoTagMAC))
        
        #return the packet in the in port
        returnOutPort = self.switch_to_parent_port[switchID]
        if returnOutPort == inPort:
            returnOutPort = OF_IN_PORT
                
        
        actions.append(ofproto_v1_3_parser.OFPActionOutput(returnOutPort))
        return actions
    
    def getDistributionActions(self,switchID):
        '''
        Get the distribution actions to the given switch and current number of flow entries.
        :param switchID: ID of current switch.
        :return: distribution flow entries to be installed
        '''
        #initialize the actions set to be empty
        actions = []

        #Distribution in 4 flow entries  - because returning the packet required extra processing and distribution requires none, first distribute the original packet and then return
        #First- send the original packet to all the distribution switches
        #Then - add info about the current switch ID (inner tag) and change the direction to be return and tag direction
        #packet arrive with inner vlan id of prev switch and dummy switch- change return direction ,set
        #the outer vlan to be curr switch and return via same port

         #if there are port to distribute to, should  add the distribution actions (send the packet to distribution as is)
        if (0 != len(self.switch_to_distribution_port[switchID])):

            #send to every switch in distribution port all the distribution ports
            for dist_port in self.switch_to_distribution_port[switchID]:
                actions.append(ofproto_v1_3_parser.OFPActionOutput(dist_port))

        #Now add the info about the current switch by popping both vlan and adding current switch tag.
        actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_src = ExtraLayers.ReturnAndTagMAC))
        # set vlan ID to be current switch with solid flag.
        actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = (retMaskedVlanID(switchID)|ExtraLayers.solidFlag)))
        # Send to ingress port.
        actions.append(ofproto_v1_3_parser.OFPActionOutput(OF_IN_PORT))        
        
        # if the there is no any RTP start in the current switch, exit
        if switchID not in self.rtp_switch_to_start_points:
            return actions
        
        # add the RTP for each RTP ID
        actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = retMaskedVlanID(ExtraLayers.NULL_ID)))
        
        entryNum = 0
        for entry in self.rtp_switch_to_start_points[switchID]:
            actions.append(ofproto_v1_3_parser.OFPActionPushVlan())
            actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_src = ExtraLayers.RTPMAC))
            actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid=retMaskedVlanID(entry['id'])))
            actions.append(ofproto_v1_3_parser.OFPActionOutput(entry['outPort']))
            #Do no pop the vlan header from the last packet send
            entryNum = entryNum + 1
            if entryNum < len(self.rtp_switch_to_start_points[switchID]):
                actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
            
        #return the actions list
        return actions
        
        
    def getDoNotDistributeActions(self,switchID):
        '''
        Get the do not distribute actions to the given switch and current number of flow entries.
        :param switchID: ID of current switch.
        :return: Do not distribute flow entries to be installed.
        '''
        
        #initialize the actions set to be empty.
        actions = []
    
        # Create the return packet - Set return And tag direaction and set the current switch ID with solid flag FALSE.

        # set vlan ID to be current switch(No solid flag).
        actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_src = ExtraLayers.ReturnAndTagMAC))
        # set vlan ID to be current switch with solid flag.
        actions.append(
            ofproto_v1_3_parser.OFPActionSetField(vlan_vid=retMaskedVlanID(switchID)))
        # Send to ingress port.
        actions.append(ofproto_v1_3_parser.OFPActionOutput(OF_IN_PORT))

        #return the actions list
        return actions

    def getReturnAndTagActions(self,switchID):
        '''
        Get the return and tag actions
        :param switchID: ID of current switch
        :return: return and tag flow entries to be installed
        '''
        actions = []
    
        #In 4 flow entries, the packet contains only tagging on last switch ID (inner tagging) need to add
        #the first switch ID (outer tagging) and change the ethertype to be dirReturnNoTag.
        # Set type of packet
        actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_src = ExtraLayers.ReturnNoTagMAC))
        #push VLAN header
        actions.append(ofproto_v1_3_parser.OFPActionPushVlan())
        #set the DirectionReturn field to be dirReturnNoTag

        #tag cuurent switch ID
        actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid=retMaskedVlanID(switchID)))
        # Send to ingress port.
        actions.append(ofproto_v1_3_parser.OFPActionOutput((self.switch_to_parent_port[switchID])))

        #return the actions list
        return actions

    def getReturnNoTagActions(self,switchID):
        '''
        Get the return no tag actions (for 4 flow entries only)
        :param switchID: ID of current switch
        :return: second return flow entries to be installed
        '''
        actions = []

        #transfer to "parent" port.
        actions.append(ofproto_v1_3_parser.OFPActionOutput((self.switch_to_parent_port[switchID])))

        #return the actions list
        return actions
