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


    def __init__ (self, portInfoGraph, OverlayGraph):
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
                    self.switch_to_parent_port[node] = 1

    def getDistributionActions(self,switchID, numberOfFlowEntries):
        '''
        Get the distribution actions to the given switch and current number of flow entries.
        :param switchID: ID of current switch.
        :param numberOfFlowEntries: 3 or 4 flow entries mode.
        :return: distribution flow entries to be installed
        '''
        #initialize the actions set to be empty
        actions = []

        #For case of 3 flow entries
        if (3 == numberOfFlowEntries):
            # Distribution in 3 flow entries case - first return the packet and then add info to each packet and distribute.

            # Packet arrive with inner vlan id of prev switch and dummy switch- change to return direction, set
            # The outer vlan to be curr switch and return via same port,

            # Pop vlan
            actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
            #set the DirectionReturn field to be dir backwards (constant for return direction of 3 flow entries)
            actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_type = ExtraLayers.dirBackwardsThreeFlowEntries))
            # push a new VLAN with ethertype of vlan
            actions.append(ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ID_ETHERTYPE_QINQ))
            # set vlan ID to be current switch (last switch field) with solid link masking
            actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = (retMaskedVlanID(switchID)|ExtraLayers.solidFlag)))
            #return via same port
            actions.append( ofproto_v1_3_parser.OFPActionOutput(OF_IN_PORT))

            #if there are port to distribute to, should add the distribution actions
            #For the distribution , for every packet, need to add vlan actions
            if (0 != len(self.switch_to_distribution_port[switchID])):

                #now after packet returned create the distribution packet. remove both vlans , push current switch
                # id and then dummy switch ID and spread to all req switches

                # Pop vlan
                actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
                #change the vlan ID from dirbackward to be vlan eth type so we will be able to pop vlan again
                actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_type = ExtraLayers.VLAN_ID_ETHERTYPE_QINQ))
                #pop second vlan
                actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
                #push vlan with vlan id of current switch
                actions.append(ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ID_ETHERTYPE_QINQ))
                actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = retMaskedVlanID(switchID)))
                #push vlan with dummy vlan because it will be removed on return path
                actions.append(ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ID_ETHERTYPE_QINQ))
                actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = retMaskedVlanID(ExtraLayers.NULL_ID)))
                #send to every switch in distribution port all the distribution ports
                #dist_ports = (self.switch_to_distribution_port)[switchID]
                for dist_port in self.switch_to_distribution_port[switchID]:
                    actions.append(ofproto_v1_3_parser.OFPActionOutput(dist_port))

        #4 flow entries case
        else:
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
            # Pop vlan
            actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
            # Pop vlan
            actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
            #set the DirectionReturn field to be dir return and tag.
            actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_type = ExtraLayers.dirReturnAndTag))
            #Set QinQ vlan type.
            actions.append(ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ID_ETHERTYPE_QINQ))
            # set vlan ID to be current switch with solid flag.
            actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = (retMaskedVlanID(switchID)|ExtraLayers.solidFlag)))
            #push vlan with dummy vlan becuase it will be removed on return (with ethertype that suit)
            actions.append(ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ETHERTYPE ))
            actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = retMaskedVlanID(ExtraLayers.NULL_ID)))
            # Send to ingress port.
            actions.append( ofproto_v1_3_parser.OFPActionOutput(OF_IN_PORT))

        #return the actions list
        return actions


    def getDoNotDistributeActions(self,switchID, numberOfFlowEntries):
        '''
        Get the do not distribute actions to the given switch and current number of flow entries.
        :param switchID: ID of current switch.
        :param numberOfFlowEntries: 3 or 4 flow entries mode.
        :return: Do not distribute flow entries to be installed.
        '''
        
        #initialize the actions set to be empty.
        actions = []
        
        #3 flow entries case.
        if (3 == numberOfFlowEntries):
            #create the return packet - set the backwards direction and add the switch id as outer tagging (without solid masking)
            #return via the input port

            # Pop vlan
            actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
            #set the DirectionReturn field to be dir backwards
            actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_type = ExtraLayers.dirBackwardsThreeFlowEntries))
            # push a new VLAN with ethertype of vlan
            actions.append(ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ID_ETHERTYPE_QINQ))
            # set vlan ID to be current switch (last switch field)
            actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = retMaskedVlanID(switchID)))
            #return via same port
            actions.append( ofproto_v1_3_parser.OFPActionOutput(OF_IN_PORT))

        else:
            # Create the return packet - Set return And tag direaction and set the current switch ID with solid flag FALSE.

            # Pop vlan
            actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
            # Pop vlan
            actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
            #set the DirectionReturn field to be  ddirReturnAndTag
            actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_type = ExtraLayers.dirReturnAndTag))
            #Push the current switch id as inner tagging
            actions.append(ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ID_ETHERTYPE_QINQ))
            # set vlan ID to be current switch(No solid flag).
            actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = (retMaskedVlanID(switchID))))
            #push vlan with dummy vlan becuase it will be removed on return.
            actions.append(ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ETHERTYPE ))
            actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = retMaskedVlanID(ExtraLayers.NULL_ID)))
            #return via the ingress port.
            actions.append( ofproto_v1_3_parser.OFPActionOutput(OF_IN_PORT))

        #return the actions list
        return actions

    def getReturnAndTagActions(self,switchID, numberOfFlowEntries):
        '''
        Get the return and tag actions (only return actions in 3 flow entries case or the first return action for 4 flow entries case)
        :param switchID: ID of current switch
        :param numberOfFlowEntries: 3 or 4 flow entries mode
        :return: return and tag flow entries to be installed
        '''
        #initialize the actions set to be empty
        actions = []
        #3 flow entries case
        if (3 == numberOfFlowEntries):
            #transfer to "parent" port as is (the packet already contains the switch ID's tagging)
            actions.append(ofproto_v1_3_parser.OFPActionOutput((self.switch_to_parent_port[switchID])))

        #4 flow entries case
        else:
            #In 4 flow entries, the packet contains only tagging on last switch ID (inner tagging) need to add
            #the first switch ID (outer tagging) and change the ethertype to be dirReturnNoTag.
            # Pop vlan
            actions.append(ofproto_v1_3_parser.OFPActionPopVlan())
            #set the DirectionReturn field to be dirReturnNoTag
            actions.append(ofproto_v1_3_parser.OFPActionSetField(eth_type = ExtraLayers.dirReturnNoTag))
            # push a new VLAN with ethertype of vlan
            actions.append(ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ID_ETHERTYPE_QINQ))
            # set vlan ID to be current switch (last switch field)
            actions.append(ofproto_v1_3_parser.OFPActionSetField(vlan_vid = retMaskedVlanID(switchID)))
            #transfer to "parent" port
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
