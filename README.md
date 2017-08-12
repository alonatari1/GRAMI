# GRAMI
This entire project is written in Python as a proof of concept for GRAMI. However, this was my first Python project so it is not written in
a "Pythonic" way.

This project was tested with Cpqd switches and RYU controller.

The files are divided between 3 projects:
Infrastructure project - For sending the probe packets, analyzing them and installing the flow entries.
                         NOTE that I also implemented a 3 flow entries version that works slightly different.
OverlayNetwork project - For creating and testing an overlay network for GRAMI.
Topology project - For parsing topology files and creating topologies for Mininet.

Infrastructure project files:

* ActionsGenerator - Generates the actions for the controller.

* Analyzer - Send probe packets for topology discovery in the controller, for flow entries and for network analysis. Analyze the results online and presents them without saving to file.

* Controller - Controller application for Ryu.

* ExtraLayers - Contains constants and creates extra layer given layers from Scapy.

* myPackets- Used by Analyzer to create and analyze the information of the probe packets.

Test related files (used to test GRAMI):
+ pingAnalyzer - Analyze the results for ping (test1).
+ pingSender - Send ICMP messages and create the listening file.

^ testAnalyzer - Analyze the results for the probe packets.
^ testSender- Automatically sends all the packets, including creating topology, installing the flow entries and sending the probe packets.

? forwardingAnalyzer - Analyze the results for pure forwarding.
? forwardingSender - Automatically sends the packets for creating the pure switching in the controller the probe packets.

OverlayNetwork project files:

* OverlayNetwork - Contains the code and algorithm for creating the overlay network.

* OverlayNetworkTester - Contains code for testing creation of different overlay networks.

Topology project files:

* CreateInfoFromGml - Code for creating a sample topology for Mininet from GML files.

