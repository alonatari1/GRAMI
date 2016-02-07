__author__ = 'ubuntu'

import networkx as nx
import os

'''This file is used to traverse the topologies and create graph for every topology.
prints the number of edges and links for the table
it prints all the edges so it can be used in the overlay network tester
it also create data to help creating files in the BasicTopo.py file '''

topologyPath = "/home/ubuntu/MyProject/MyTopologies/topologyZoo/"
files = os.listdir(topologyPath)
for file in files:

    #set the topology
    fileName = topologyPath + file
    G = nx.read_gml(fileName)
    fixedEdges = []
    for edge in G.edges():
        fixedEdges.append ((edge[0]+1, edge[1]+1))

    print "The file is " + fileName
    #Get the size of the network
    print "The number of edges is" , len(fixedEdges) , "and number of nodes is" , len(G.nodes())

    #Get the edges for running the overlay network
    print "Edges for the overlay network code"
    print fixedEdges

    #After finding the MPs with overlay network tester we can use this script to easily create the mininet code
    print "Info for creating the mininet network code"
    for node in G.nodes():
        print "self.addSwitch( 's"+str(node+1)+"' ),"
    for edge in G.edges():
        print "self.addLink( s["+str(edge[0])+"], s["+str(edge[1])+"], delay=defDelay, bw = defBW)"
