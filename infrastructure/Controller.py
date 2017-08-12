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
        
        self.rtp_id_to_path = {1: [1, 2, 3, 1]}#, 2: [1, 2, 4, 3, 1]}

        #self.rtp_id_to_path = {}
        self.rtp_switch_to_start_points = {}
        self.rtp_switch_to_forward = {}
        
        self.rtp_id_to_path_with_ports = {}
        
        self.h1Toh2Path = { 1 : (1,2), 2 : (1,2), 3: (1,2), 4 : (1,2) }
        
        # Saving the graph with the topology, will be updated on demand.
        self.topologyGraph = nx.Graph()
        
    def installSimpleForwardRules(self, datapath):
        if datapath.id not in self.h1Toh2Path:
            return
        toH2Port = self.h1Toh2Path[datapath.id][1]
        toH1Port = self.h1Toh2Path[datapath.id][0]
        print "Installing rules to {0}".format(datapath.id)
        
        h1MacAddress = "00:0c:29:8a:c8:66"
        h2MacAddress = "00:0c:29:8a:c8:ff"
        
        match = ofproto_v1_3_parser.OFPMatch(eth_src = h1MacAddress )

        # The instructions are apply actions with the distribution Actions - apply actions by order.
        instructions = [ofproto_v1_3_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS, 
                                                                    [ofproto_v1_3_parser.OFPActionOutput(toH2Port)])]

        # Prepare the flow entry (NOTE: higher priority).
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath, priority=3,
                                             match=match, instructions=instructions)
        datapath.send_msg(mod)

        match = ofproto_v1_3_parser.OFPMatch(eth_src = h2MacAddress)


        # The instructions are apply actions with the distribution Actions - apply actions by order.
        instructions = [ofproto_v1_3_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS, 
                                                                    [ofproto_v1_3_parser.OFPActionOutput(toH1Port)])]

        # Prepare the flow entry (NOTE: higher priority).
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath, priority=3,
                                             match=match, instructions=instructions)
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
        
        self.installRTPForwardFlowEntries(datapath)
        self.installRTPReturnFlowEntries(datapath)
        
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
        

        print MPs, type(MPs), numberOfMPs, type(numberOfMPs)
        for link in self.topologyGraph.edges(data= True):
            print link
        
        '''
        #
        #print myNet.edges()
        '''

        # According to the given network create the overlay graph.
        OGMyNet = OverlayNetwork.OverlayNetworkGraph(self.topologyGraph, numberOfMPs, MPs)

        # Create the action generator for generation of action lists for every switch (get the parent and distribution ports).
        self.actionsGenerator = ActionsGenerator.ActionsGenerator(self.topologyGraph, OGMyNet, self.rtp_switch_to_start_points)
        self.getRTPsPathWithPorts()
           
        
        print "*** the MPs are"
        print OGMyNet.MPs
        print "*** father port for switch ID"
        print self.actionsGenerator.switch_to_parent_port
        print "*** distribution ports for switch ID"
        print self.actionsGenerator.switch_to_distribution_port
        print "*** RTPS"
        print self.rtp_id_to_path
        print self.rtp_id_to_path_with_ports
        print self.rtp_switch_to_start_points
        print self.rtp_switch_to_forward
        
        # Install all the flow entries for every switch in the network.
        for switch in OGMyNet.graph.nodes():
            self.installGRAMIFlowEntriesOnSwitch(self.id_to_datapath[switch])

    
    def appendRTPEntry(self, path, RTPID):
        """
        add a RTP caclulation.
        :param path: an array of the RTP switches ID path.
        :param RTPID: the id of rtp.
        :return:
        """
        
        print "*** Adding RTP <{0}> with path {1}".format(RTPID, path)
        
        if len(path) <= 2:
            print "*** Error: invalid path length"
            return
        if path[0] != path[-1]:
            print "*** Error: path is not a circle"
            return
        
        self.rtp_id_to_path[RTPID] = path
    
    def getRTPsPathWithPorts(self):
        """
        get full RTP path with in and out ports.
        :return:
        """
        # Iterate over all the RTPs
        for id, path in self.rtp_id_to_path.iteritems():
            linksWithPorts = []
            # For each link in RTP
            for idIndex in range(0, len(path)-1):
                found = False
                currentId = path[idIndex]
                nextId = path[idIndex+1]
                # add the link src and dst port to the switch
                for link in self.topologyGraph.edges(data= True):
                    if ((link[2]['dst'] == currentId) and (link[2]['src'] == nextId)):
                        linksWithPorts.append({'src' : currentId,
                                               'dst' : nextId, 
                                               'srcPort' : link[2]['dstPort'], 
                                               'dstPort' : link[2]['srcPort']})
                        found = True
                        break
                    elif ((link[2]['src'] == currentId) and (link[2]['dst'] == nextId)):
                        linksWithPorts.append(link[2])
                        found = True
                        break
                if not found:
                    print "bad {0} {1}".format(currentId, nextId)
            # add the full path with the ID 
            self.rtp_id_to_path_with_ports[id] = linksWithPorts
        
        # create start rtp switches dictionaries
        for id, RTP in self.rtp_id_to_path_with_ports.iteritems():
            if RTP[0]['src'] not in self.rtp_switch_to_start_points:
                self.rtp_switch_to_start_points[RTP[0]['src']] = []
            self.rtp_switch_to_start_points[RTP[0]['src']].append( { 'id': id, 'outPort': RTP[0]['srcPort'], 'inPort': RTP[-1]['dstPort'] } )
            for i in range(1,len(RTP)):
                if RTP[i]['src'] not in self.rtp_switch_to_forward:
                    self.rtp_switch_to_forward[RTP[i]['src']] = []
                self.rtp_switch_to_forward[RTP[i]['src']].append( { 'id': id, 'outPort': RTP[i]['srcPort'], 'inPort': RTP[i-1]['dstPort'] } )
         
      
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
        self.installSimpleForwardRules(datapath)

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
        ForwardingMatch = ofproto_v1_3_parser.OFPMatch(in_port = parentPort, eth_src = ExtraLayers.DistributeMAC,
                                                       vlan_vid=(0x1000, 0x1000))

        # Get the distribution actions.
        distributionActions = self.actionsGenerator.getDistributionActions(switchID)

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
        doNotDistributeMatch = ofproto_v1_3_parser.OFPMatch(eth_src = ExtraLayers.DistributeMAC,
                                                       vlan_vid=(0x1000, 0x1000))

        # Get the do not distribute actions.
        doNotDistributeActions = self.actionsGenerator.getDoNotDistributeActions(switchID)

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
   
        # Equivalent to return with setIDFlag TRUE.
        ethTypeMatch = ExtraLayers.dirReturnAndTag

        # Get the switch ID.
        switchID = datapath.id

        # Match if this is a return and tag probe pacekt (4 flow entries case) or dir backwards if 3 flow entries.
        FirstReturnMatch = ofproto_v1_3_parser.OFPMatch(eth_src = ExtraLayers.ReturnAndTagMAC,
                                                       vlan_vid=(0x1000, 0x1000))

        # Get actions.
        returnAndTagActions = self.actionsGenerator.getReturnAndTagActions(switchID)

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

        # Get the switch ID
        switchID = datapath.id

        # Match if the packet has return no tag Ethertype. Equivalent to return with setIDFlag TRUE.
        returnNoTagMatch = ofproto_v1_3_parser.OFPMatch(eth_src = ExtraLayers.ReturnNoTagMAC,
                                                       vlan_vid=(0x1000, 0x1000))

        # Get actions.
        returnNoTagActions = self.actionsGenerator.getReturnNoTagActions(switchID)

        # The instructions are apply actions with the return no tag Actions - apply actions by order.
        SecondReturnInst = [ofproto_v1_3_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS,returnNoTagActions)]

        # Prepare the flow entry.
        mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath, priority=NORMAL_PRIO,
                                             match=returnNoTagMatch, instructions=SecondReturnInst)
        datapath.send_msg(mod)


    def installRTPForwardFlowEntries(self, datapath):
        """
        install the RTP foward packet entries.
        :param datapath: switch datapath.
        :return:
        """
        
        # Get the switch ID
        switchID = datapath.id
        
        if switchID not in self.rtp_switch_to_forward:
            return
        
        for entry in self.rtp_switch_to_forward[switchID]:
            # Match if the packet has return no tag Ethertype. Equivalent to return with setIDFlag TRUE.
            RTPForwardMatch = ofproto_v1_3_parser.OFPMatch(eth_src = ExtraLayers.RTPMAC,
                                                       vlan_vid=ActionsGenerator.retMaskedVlanID(entry['id']))

            # Get actions.
            RTPForwardActions = self.actionsGenerator.getRTPForwardAction(entry['outPort'])

            # The instructions are apply actions with the return no tag Actions - apply actions by order.
            SecondReturnInst = [ofproto_v1_3_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS,RTPForwardActions)]

            # Prepare the flow entry.
            mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath, priority=NORMAL_PRIO,
                                                 match=RTPForwardMatch, instructions=SecondReturnInst)
            datapath.send_msg(mod)
        
    def installRTPReturnFlowEntries(self, datapath):
        """
        Install RTP entry when the RTP path end, and we need ti return the packet to MP
        :param datapath: switch datapath.
        :return:
        """
        # Get the switch ID
        switchID = datapath.id
        
        if switchID not in self.rtp_switch_to_start_points:
            return
        
        for entry in self.rtp_switch_to_start_points[switchID]:
            print "match id {0} on switch {1}".format(entry['id'],switchID)
            # Match if the packet has return no tag Ethertype. Equivalent to return with setIDFlag TRUE.
            RTPReturnMatch = ofproto_v1_3_parser.OFPMatch(eth_src = ExtraLayers.RTPMAC,
                                                       vlan_vid=ActionsGenerator.retMaskedVlanID(entry['id']))

            
            
            # Get actions.
            RTPReturnActions = self.actionsGenerator.getRTPReturnActions(switchID,entry['inPort'])

            # The instructions are apply actions with the return no tag Actions - apply actions by order.
            SecondReturnInst = [ofproto_v1_3_parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS,RTPReturnActions)]

            # Prepare the flow entry.
            mod = ofproto_v1_3_parser.OFPFlowMod(datapath=datapath, priority=NORMAL_PRIO,
                                                 match=RTPReturnMatch, instructions=SecondReturnInst)
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
            ExtraLayers.getMeasurementRound(msg.data)
            self.updateTopology()
            return

        # If this is an analyze message, get the MPs and number of MPs and send them to the analyzing function.
        if (ExtraLayers.analyzeEtherMAC == src):
            numberOfMPs, MPs = ExtraLayers.getMPsInfoFromPacket(pkt)
            self.analyzeAndInstallFlowEntries(numberOfMPs, MPs)
            return
        
        # If this is an append RTP message, get the ID and the path of RTP.        
        if (ExtraLayers.appendRTPMAC == src):
            path, RTPID = ExtraLayers.getRTPInfoFromPacket(pkt)
            self.appendRTPEntry(path, RTPID)
            return

        return
