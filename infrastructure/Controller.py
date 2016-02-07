from bsddb.dbtables import ExactCond
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.topology.switches import Switches
import ExtraLayers #For info about our extra layer being sent
import ActionsGenerator
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
import networkx as nx
import sys
sys.path.append('/home/ubuntu/PycharmProjects/overlayNetwork')
import OverlayNetwork
import time

'''priorities'''
NO_MATCH_PRIO = 0 # When we have no match, send to the controller.
NORMAL_SWITCH_FORWARDING_PRIO = NO_MATCH_PRIO + 1 # Normal L2 forwarding flow entries.
                                                  # Used for creating the RTPs.
NORMAL_PRIO = NORMAL_SWITCH_FORWARDING_PRIO + 1 # Normal GRAMI flow entry priority
DISTRIBUTE_PRIO = NORMAL_PRIO + 1 # Higher priority of distribution


class GRAMIController(app_manager.RyuApp):
    """
    Ryu controller implementation.
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]  # List of supported versions, currently only 1.3

    #Initialize the switch
    def __init__(self, *args, **kwargs):
        """
        Initialize the switch, extra information for installing the relevant flow entries.
        :param args:
        :param kwargs:
        :return:
        """

        super(GRAMIController, self).__init__(*args, **kwargs)

        # Holds the mapping between the mac of thw switch (Switch ID) to the egress port for building the overlay network.
        self.mac_to_port = {}

        # Implement the topology application to be the same app.
        self.topology_api_app = self

        # Holds the mapping between the switch ID and the datapath.
        self.id_to_datapath = {}

        # Saving the graph with the topology, will be updated on demand.
        self.topologyGraph = nx.Graph()

        # Save how many flow entries to install on every switch (3 or 4).
        self.numberOfFlowEntries = 4

    def installTestStarFlowEntries(self):
        """
        Code written for specific test on start topology. (Measure duplication and tagging time).
        :return:
        """

        datapath1 = self.id_to_datapath[1]
        datapath2 = self.id_to_datapath[2]

        # Install the flow entries on the MP.
        Match = ofproto_v1_3_parser.OFPMatch(in_port = 1, eth_type = ExtraLayers.typeForTestingTaggingAndDuplicationTime)
        Actions = [ofproto_v1_3_parser.OFPActionOutput(0xfffffffd), ofproto_v1_3_parser.OFPActionOutput(0xfffffffd),
                   ofproto_v1_3_parser.OFPActionPopVlan(),
                   ofproto_v1_3_parser.OFPActionSetField(eth_type = ExtraLayers.dirBackwardsThreeFlowEntries),
                   ofproto_v1_3_parser.OFPActionPushVlan(ethertype = ExtraLayers.VLAN_ID_ETHERTYPE_QINQ),
                   ofproto_v1_3_parser.OFPActionSetField(vlan_vid = 1),
                   ofproto_v1_3_parser.OFPActionOutput(0xfffffffd)]
        Inst = [ofproto_v1_3_parser.OFPInstructionActions(datapath1.ofproto.OFPIT_APPLY_ACTIONS,Actions)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath1, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=Match, instructions=Inst )
        datapath1.send_msg(mod)


    #Only for topology2 pure forwarding for 4 paths, install all the rules
    def installPureForwardingTopo2(self):
        """
        Used to create specific path for pure forwarding to check the overhead of GRAMI.
        Was written specifically for topology number 2.
        :return:
        """

        # Datapaths
        datapath1 = self.id_to_datapath[1]
        datapath2 = self.id_to_datapath[2]
        datapath3 = self.id_to_datapath[3]
        datapath14 = self.id_to_datapath[14]
        datapath16 = self.id_to_datapath[16]
        datapath17 = self.id_to_datapath[17]
        datapath20 = self.id_to_datapath[20]

        ##################################################
        #Path Len 1 (h1 (0) -> s2 (1))
        MatchLen1s2toh1 = ofproto_v1_3_parser.OFPMatch(in_port = 1, eth_type = ExtraLayers.PureForwardingLen1EtherType)
        ActionsLen1s2toh1 = [ofproto_v1_3_parser.OFPActionOutput(0xfffffff8)]
        InstLen1s2toh1 = [ofproto_v1_3_parser.OFPInstructionActions(datapath2.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen1s2toh1)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath2, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen1s2toh1, instructions=InstLen1s2toh1 )
        datapath2.send_msg(mod) #send the message

        ##################################################
        #the path is describes as node(port) -> node(inPort, outPort) -> node(inPort)
        #Should install flow entries for both path forward and path return back to the host
        #Path len 2 (h1 (0) -> s2 (1,4) -> s20(2))
        MatchLen1s2tos20 = ofproto_v1_3_parser.OFPMatch(in_port = 1, eth_type = ExtraLayers.PureForwardingLen2EtherType)
        ActionsLen1s2tos20 = [ofproto_v1_3_parser.OFPActionOutput(4)]
        InstLen1s2tos20 = [ofproto_v1_3_parser.OFPInstructionActions(datapath2.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen1s2tos20)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath2, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen1s2tos20, instructions=InstLen1s2tos20 )
        datapath2.send_msg(mod) #send the message


        MatchLen1s20tos2 = ofproto_v1_3_parser.OFPMatch(in_port = 2, eth_type = ExtraLayers.PureForwardingLen2EtherType)
        ActionsLen1s20tos2 = [ofproto_v1_3_parser.OFPActionOutput(0xfffffff8)]
        InstLen1s20tos2 = [ofproto_v1_3_parser.OFPInstructionActions(datapath20.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen1s20tos2)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath20, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen1s20tos2, instructions=InstLen1s20tos2 )
        datapath20.send_msg(mod) #send the message

        MatchLen1s2toh1 = ofproto_v1_3_parser.OFPMatch(in_port = 4, eth_type = ExtraLayers.PureForwardingLen2EtherType)
        ActionsLen1s2toh1 = [ofproto_v1_3_parser.OFPActionOutput(1)]
        InstLen1s2toh1 = [ofproto_v1_3_parser.OFPInstructionActions(datapath2.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen1s2toh1)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath2, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen1s2toh1, instructions=InstLen1s2toh1 )
        datapath2.send_msg(mod) #send the message

        ##################################################
        #Path len 3 (h1(0)-> s2(1,2) -> s1(1,2) -> s3(1))
        MatchLen3s2tos1 = ofproto_v1_3_parser.OFPMatch(in_port = 1, eth_type = ExtraLayers.PureForwardingLen3EtherType)
        ActionsLen3s2tos1 = [ofproto_v1_3_parser.OFPActionOutput(2)]
        InstLen3s2tos1 = [ofproto_v1_3_parser.OFPInstructionActions(datapath2.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen3s2tos1)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath2, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen3s2tos1, instructions=InstLen3s2tos1 )
        datapath2.send_msg(mod) #send the message


        MatchLen3s1tos3 = ofproto_v1_3_parser.OFPMatch(in_port = 1, eth_type = ExtraLayers.PureForwardingLen3EtherType)
        ActionsLen3s1tos3 = [ofproto_v1_3_parser.OFPActionOutput(2)]
        InstLen3s1tos3 = [ofproto_v1_3_parser.OFPInstructionActions(datapath1.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen3s1tos3)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath1, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen3s1tos3, instructions=InstLen3s1tos3 )
        datapath1.send_msg(mod) #send the message


        MatchLen3s3tos1 = ofproto_v1_3_parser.OFPMatch(in_port = 1, eth_type = ExtraLayers.PureForwardingLen3EtherType)
        ActionsLen3s3tos1 = [ofproto_v1_3_parser.OFPActionOutput(0xfffffff8)]
        InstLen3s3tos1 = [ofproto_v1_3_parser.OFPInstructionActions(datapath3.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen3s3tos1)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath3, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen3s3tos1, instructions=InstLen3s3tos1 )
        datapath3.send_msg(mod) #send the message

        MatchLen3s1tos2 = ofproto_v1_3_parser.OFPMatch(in_port = 2, eth_type = ExtraLayers.PureForwardingLen3EtherType)
        ActionsLen3s1tos2 = [ofproto_v1_3_parser.OFPActionOutput(1)]
        InstLen3s1tos2 = [ofproto_v1_3_parser.OFPInstructionActions(datapath1.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen3s1tos2)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath1, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen3s1tos2, instructions=InstLen3s1tos2 )
        datapath1.send_msg(mod) #send the message

        MatchLen3s2toh1 = ofproto_v1_3_parser.OFPMatch(in_port = 2, eth_type = ExtraLayers.PureForwardingLen3EtherType)
        ActionsLen3s2toh1 = [ofproto_v1_3_parser.OFPActionOutput(1)]
        InstLen3s2toh1 = [ofproto_v1_3_parser.OFPInstructionActions(datapath2.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen3s2toh1)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath2, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen3s2toh1, instructions=InstLen3s2toh1 )
        datapath2.send_msg(mod) #send the message

        ##################################################
        #Path len 4 (h1 (0) -> s2 (1,3) -> s17(2,4) -> s14(3,5) -> s16(1))
        MatchLen4s2tos17 = ofproto_v1_3_parser.OFPMatch(in_port = 1, eth_type = ExtraLayers.PureForwardingLen4EtherType)
        ActionsLen4s2tos17 = [ofproto_v1_3_parser.OFPActionOutput(3)]
        InstLen4s2tos17 = [ofproto_v1_3_parser.OFPInstructionActions(datapath2.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen4s2tos17)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath2, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen4s2tos17, instructions=InstLen4s2tos17 )
        datapath2.send_msg(mod) #send the message


        MatchLen4s17tos14 = ofproto_v1_3_parser.OFPMatch(in_port = 2, eth_type = ExtraLayers.PureForwardingLen4EtherType)
        ActionsLen4s17tos14 = [ofproto_v1_3_parser.OFPActionOutput(4)]
        InstLen4s17tos14 = [ofproto_v1_3_parser.OFPInstructionActions(datapath17.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen4s17tos14)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath17, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen4s17tos14, instructions=InstLen4s17tos14 )
        datapath17.send_msg(mod) #send the message


        MatchLen4s14tos16 = ofproto_v1_3_parser.OFPMatch(in_port = 3, eth_type = ExtraLayers.PureForwardingLen4EtherType)
        ActionsLen4s14tos16 = [ofproto_v1_3_parser.OFPActionOutput(5)]
        InstLen4s14tos16 = [ofproto_v1_3_parser.OFPInstructionActions(datapath14.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen4s14tos16)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath14, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen4s14tos16, instructions=InstLen4s14tos16 )
        datapath14.send_msg(mod) #send the message


        MatchLen4s16tos14 = ofproto_v1_3_parser.OFPMatch(in_port = 1, eth_type = ExtraLayers.PureForwardingLen4EtherType)
        ActionsLen4s16tos14 = [ofproto_v1_3_parser.OFPActionOutput(0xfffffff8)]
        InstLen4s16tos14 = [ofproto_v1_3_parser.OFPInstructionActions(datapath16.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen4s16tos14)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath16, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen4s16tos14, instructions=InstLen4s16tos14 )
        datapath16.send_msg(mod) #send the message

        MatchLen4s14tos17 = ofproto_v1_3_parser.OFPMatch(in_port = 5, eth_type = ExtraLayers.PureForwardingLen4EtherType)
        ActionsLen4s14tos17 = [ofproto_v1_3_parser.OFPActionOutput(3)]
        InstLen4s14tos17 = [ofproto_v1_3_parser.OFPInstructionActions(datapath14.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen4s14tos17)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath14, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen4s14tos17, instructions=InstLen4s14tos17 )
        datapath14.send_msg(mod) #send the message

        MatchLen4s17tos2 = ofproto_v1_3_parser.OFPMatch(in_port = 4, eth_type = ExtraLayers.PureForwardingLen4EtherType)
        ActionsLen4s17tos2 = [ofproto_v1_3_parser.OFPActionOutput(2)]
        InstLen4s17tos2 = [ofproto_v1_3_parser.OFPInstructionActions(datapath17.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen4s17tos2)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath17, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen4s17tos2, instructions=InstLen4s17tos2 )
        datapath17.send_msg(mod) #send the message

        MatchLen4s2toh1 = ofproto_v1_3_parser.OFPMatch(in_port = 3, eth_type = ExtraLayers.PureForwardingLen4EtherType)
        ActionsLen4s2toh1 = [ofproto_v1_3_parser.OFPActionOutput(1)]
        InstLen4s2toh1 = [ofproto_v1_3_parser.OFPInstructionActions(datapath2.ofproto.OFPIT_APPLY_ACTIONS,ActionsLen4s2toh1)]
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath2, priority= NORMAL_SWITCH_FORWARDING_PRIO,
                                             match=MatchLen4s2toh1, instructions=InstLen4s2toh1 )
        datapath2.send_msg(mod) #send the message

    def installDistributeFlowEntry(self, datapath):
        '''
        Install the distribution flow entry, Same fore the ccase of 3 or 4 flow entries.
        :param datapath: datapath which represent the switch to install the flow entries on.
        '''

        # Get the switch ID.
        switchID = datapath.id

        # Get the parent port for the match.
        parentPort = (self.actionsGenerator.switch_to_parent_port[switchID])

        # Match if the probe packet is directed forward (equivalent to forward and setIDFlag TRUE) and the ingress port is
        # the parent port. For safety , added also NULL ID in vlan.
        ForwardingMatch = ofproto_v1_3_parser.OFPMatch(in_port = parentPort, eth_type = ExtraLayers.dirForward, vlan_vid =  ExtraLayers.NULL_ID)

        # Get the distribution actions.
        distributionActions = self.actionsGenerator.getDistributionActions(switchID, self.numberOfFlowEntries)

        # The instructions are apply actions with the distribution Actions - apply actions by order.
        forwardingInst = [ofproto_v1_3_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS, distributionActions)]

        # Prepare the flow entry (NOTE: higher priority).
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath, priority=DISTRIBUTE_PRIO,
                                             match=ForwardingMatch, instructions=forwardingInst)
        datapath.send_msg(mod)

    def installDoNotDistributeFlowEntry(self,datapath):
        '''
        Install the do not distribute flow entry. for matching the flow entries are the same for the case of 3 or 4 flow entries.
        :param datapath: datapath which represent the switch to install the flow entries on.
        '''

        #Get the switch ID
        switchID = datapath.id

        # Match if the probe packet is directed forward (equivalent to forward and setIDFlag TRUE).
        doNotDistributeMatch = ofproto_v1_3_parser.OFPMatch(eth_type = ExtraLayers.dirForward)

        # Get the do not distribute actions.
        doNotDistributeActions = self.actionsGenerator.getDoNotDistributeActions(switchID,self.numberOfFlowEntries)

        # The instructions are apply actions with the return and tag Actions - apply actions by order.
        doNotDistributeInst = [ofproto_v1_3_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS,doNotDistributeActions)]

        # Prepare the flow entry.
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath, priority=NORMAL_PRIO,
                                             match=doNotDistributeMatch, instructions=doNotDistributeInst)
        datapath.send_msg(mod)

    def installReturnAndTagFlowEntry(self, datapath):
        '''
        Install return and tag flow entry. This flow entry is different for the 3 or 4 flow entries case, and the matching is different
        :param datapath: datapath which represent the switch to install the flow entries on.
        '''

        # Get the ethertype to match on for the case of 3 flow entries or 4 flow entries
        if (3 == self.numberOfFlowEntries):
            ethTypeMatch = ExtraLayers.dirBackwardsThreeFlowEntries
        else:
            # Equivalent to return with setIDFlag TRUE.
            ethTypeMatch = ExtraLayers.dirReturnAndTag

        # Get the switch ID.
        switchID = datapath.id

        # Match if this is a return and tag probe pacekt (4 flow entries case) or dir backwards if 3 flow entries.
        FirstReturnMatch = ofproto_v1_3_parser.OFPMatch(eth_type = ethTypeMatch)

        # Get actions.
        returnAndTagActions = self.actionsGenerator.getReturnAndTagActions(switchID,self.numberOfFlowEntries)

        # The instructions are apply actions with the return and tag Actions - apply actions by order.
        returnAndTagActions = [ofproto_v1_3_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS,returnAndTagActions)]

        # Prepare the flow entry.#prepare the message for flow installing on given switch, priority, match and instructions
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath, priority=NORMAL_PRIO,
                                             match=FirstReturnMatch, instructions=returnAndTagActions)
        datapath.send_msg(mod)

    def installReturnNoTagFlowEntry(self, datapath):
        '''
        Install the return no tag flow entry - relevant for the case of 4 flow entries only.
        :param datapath: datapath which represent the switch to install the flow entries on.
        '''

        #If we are working with 3 flow entries only, return because need to install nothing.
        if (3 == self.numberOfFlowEntries):
            return

        # Get the switch ID
        switchID = datapath.id

        # Match if the packet has return no tag Ethertype. Equivalent to return with setIDFlag TRUE.
        returnNoTagMatch = ofproto_v1_3_parser.OFPMatch(eth_type = ExtraLayers.dirReturnNoTag)

        # Get actions.
        returnNoTagActions = self.actionsGenerator.getReturnNoTagActions(switchID)

        # The instructions are apply actions with the return no tag Actions - apply actions by order.
        SecondReturnInst = [ofproto_v1_3_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS,returnNoTagActions)]

        # Prepare the flow entry.
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath, priority=NORMAL_PRIO,
                                             match=returnNoTagMatch, instructions=SecondReturnInst)
        datapath.send_msg(mod)



    #install all of GRAMI's flow entries
    def installGRAMIFlowEntriesOnSwitch(self, datapath):
        """
        Install flow enries on the given switch.
        :param datapath: datapath which represent the switch to install the flow entries on.
        :return:
        """

        print "Start time" , time.time()
        self.installDistributeFlowEntry(datapath)
        self.installReturnAndTagFlowEntry(datapath)
        self.installReturnNoTagFlowEntry(datapath)
        self.installDoNotDistributeFlowEntry(datapath)
        print "End time" , time.time()

    def sendTopologyMessage(self, port, switchID):
        """
        Send a message from the switchID via the port to discover which switch is connected to this port.
        :param port: specific port.
        :param switchID: given switch ID.
        :return:
        """

        #Create a message that will be sent to the via specific port to discover to whom it is connected
        message = ExtraLayers.createTopologyMessage(str(port),str(switchID))

        # The representing data path.
        datapath = self.id_to_datapath[switchID]

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # The action is just to send the message via the given port.
        actions = [parser.OFPActionOutput(port = port)]

        # Create the openflow message.
        out = parser.OFPPacketOut(datapath=datapath,buffer_id = ofproto.OFP_NO_BUFFER,
                                  in_port= ofproto.OFPP_CONTROLLER, actions=actions, data=message)
        datapath.send_msg(out)

    def addLink(self, packet, dstSwitch, dstPort):
        """
        Add link to the network graph.
        Get the packet with data on source port and switch and the the dst switch and port are the destination of this packet.
        Add the information as an edge to the graph which represents the network topology.
        :param packet: The packet received with information about the link.
        :param dstSwitch: The destination switch of that packet.
        :param dstPort: The destination port of that packet.
        :return:
        """

        srcSwitch, srcPort = ExtraLayers.getToplogyData(packet)
        self.topologyGraph.add_edge(srcSwitch,dstSwitch,src = srcSwitch, srcPort = srcPort, dst = dstSwitch, dstPort = dstPort)

    def updateTopology(self):
        """
        Create a topology to represent the netowkr graph.
        :return:
        """

        # Clear the graph.
        self.topologyGraph.clear()

        # Get all the switches (send a message to get all the switches and add them as nodes to the network topology graph).
        switch_list = get_switch(self.topology_api_app, None)

        # Traverse all the switches to find their neighbors.
        for switch in switch_list:
            self.topologyGraph.add_node(switch.dp.id)

            # Traverse all the ports and send discovery messages from them to find to whom they are connected.
            for port in switch.ports:
                self.sendTopologyMessage(port.port_no, switch.dp.id)

        print "**********List of switches"
        print self.topologyGraph.nodes()

    def analyzeAndInstallFlowEntries(self, numberOfMPs, MPs):
        """
        Analyze the network, calculate the overlay network and install the flow entries on network switches.
        :param numberOfMPs: How many MPs to use.
        :param MPs: The location for the MPs.
        :return:
        """

        print "**********List of links with ports"
        for link in self.topologyGraph.edges(data= True):
            print link

        '''
        #print MPs, type(MPs), numberOfMPs, type(numberOfMPs)
        #print myNet.edges()
        '''

        # According to the given network create the overlay graph.
        OGMyNet = OverlayNetwork.OverlayNetworkGraph(self.topologyGraph, numberOfMPs, MPs)

        # Create the action generator for generation of action lists for every switch (get the parent and distribution ports).
        self.actionsGenerator = ActionsGenerator.ActionsGenerator(self.topologyGraph, OGMyNet)

        print "*** the MPs are"
        print OGMyNet.MPs
        print "*** father port for switch ID"
        print self.actionsGenerator.switch_to_parent_port
        print "*** distribution ports for switch ID"
        print self.actionsGenerator.switch_to_distribution_port

        # Install all the flow entries for every switch in the network.
        for switch in OGMyNet.graph.nodes():
            self.installGRAMIFlowEntriesOnSwitch(self.id_to_datapath[switch])


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Will be called on switch features event. Will happen to every switch when it will replace configurations with
        the controller.
        :param ev:
        :return:
        """

        datapath = ev.msg.datapath #Corresponding to the switch.
        ofproto = datapath.ofproto # The protocol (1.3).
        parser = datapath.ofproto_parser # Parsing module.

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, NO_MATCH_PRIO, match, actions)

        # Add datapath to switch mapping
        self.id_to_datapath[datapath.id] = datapath

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """
        Add flow entry function, with all the information of the flow entry.
        :param datapath:
        :param priority:
        :param match:
        :param actions:
        :param buffer_id:
        :return:
        """

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
        Will be called on packet in event.
        :param ev:
        :return:
        """

        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        # If this is a topology discovery message, add a link to the network graph.
        if (ExtraLayers.topologyControllerEtherMAC == src):
            self.addLink(pkt,datapath.id,in_port)
            return

        # If this is a update topology message, get also the number of flow entries and update the topology.
        if (ExtraLayers.topologyHostEtherMAC == src):
            self.numberOfFlowEntries = ExtraLayers.getMeasurementRound(msg.data)
            self.updateTopology()
            return

        # If this is an analyze message, get the MPs and number of MPs and send them to the analyzing function.
        if (ExtraLayers.analyzeEtherMAC == src):
            numberOfMPs, MPs = ExtraLayers.getMPsInfoFromPacket(pkt)
            self.analyzeAndInstallFlowEntries(numberOfMPs, MPs)
            return

        '''# If this is an install pure forwarding flow entries for topology 2
        if (ExtraLayers.pureForwardingMac == src):
            self.installPureForwardingTopo2()
            return

        # If this is for star topology tests.
        if (ExtraLayers.testStarMAC == src):
            self.installTestStarFlowEntries()
            return


        print "didnt got here" '''

        # The messages above were created to be analyzed in the controller and shouldn't be forwarded.

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # Learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, NORMAL_SWITCH_FORWARDING_PRIO, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, NORMAL_SWITCH_FORWARDING_PRIO, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)

        datapath.send_msg(out)