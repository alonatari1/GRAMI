__author__ = 'ubuntu'

import networkx as nx
import OverlayNetwork

'''This file create some graphs to the the Overlay Network module'''

#######create some graphs#######
#create complete graph
completeGraph = nx.complete_graph(5)

#Create graph of tree but not full
treeGraph = nx.Graph()
treeGraph.add_edges_from([(1,2),(1,3),(1,4),(2,5),(2,6),(3,7),(4,8),(4,9),(4,10),(5,11),(5,12),(10,13),(13,14)])

#create same graph of tree but one subtree contains loop
treeLoopGraph = nx.Graph()
treeLoopGraph.add_edges_from([(1,2),(1,3),(1,4),(2,5),(2,6),(3,7),(4,8),(4,9),(4,10),(5,11),(5,12),(10,13),(11,12),(13,14)])

#create my graph (the Graph I worked with for testing the controller)
myGraph = nx.Graph()
myGraph.add_edges_from([(1,2),(2,3),(2,4)])

#create my graph with loop (The graph from presentation)
myLoopGraph = nx.Graph()
myLoopGraph.add_edges_from([(1,2),(2,7),(2,3),(3,4),(3,5),(3,6),(4,5),(4,6),(5,9),(6,7),(6,8),(6,9),(7,9)])

#another graph for tests
testGraph1 = nx.Graph()
testGraph1.add_edges_from([(3,4),(3,5),(3,6),(5,9)])

#cycle graph
cycleGraph = nx.Graph()
cycleGraph.add_path([1,2,3,4,5,6,7,8,9])
cycleGraph.add_edge(9,1)

#cycle graph with string
cycleStringGraph = nx.Graph()
cycleStringGraph.add_path([1,2,3,4,5,6,7,8,9])
cycleStringGraph.add_edge(9,1)
cycleStringGraph.add_edge(3,7)

#create my Graph for infocom paper
paper0Graph = nx.Graph()
paper0Graph.add_edges_from([(1,2),(2,3),(3,4),(4,5)])

paper1Graph = nx.Graph()
paper1Graph.add_edges_from([(1, 2), (1, 3), (1, 7), (1, 8), (2, 7), (3, 4), (3, 7), (3, 10), (3, 16), (3, 17), (3, 18),
                            (3, 21), (3, 22), (4, 9), (4, 10), (4, 7), (5, 6), (5, 8), (6, 8), (6, 9), (6, 10), (6, 14),
                            (6, 15), (7, 8), (9, 10), (9, 14), (10, 14), (10, 17), (10, 23), (11, 12), (11, 14), (11, 15),
                            (12, 13), (12, 14), (12, 15), (13, 25), (13, 14), (14, 16), (14, 17), (14, 18), (14, 23),
                            (16, 17), (16, 18), (16, 22), (17, 18), (18, 19), (18, 20), (18, 21), (18, 22), (18, 23),
                            (19, 22), (20, 21), (22, 23), (23, 24), (23, 25), (23, 25), (24, 25)])

paper2Graph = nx.Graph()
paper2Graph.add_edges_from([(1, 2), (1, 3), (1, 6), (2, 17), (2, 20), (3, 25), (3, 20), (4, 21), (4, 15), (5, 17), (5, 14),
                            (6, 9), (6, 19), (6, 8), (7, 8), (9, 26), (9, 10), (10, 18), (11, 14), (12, 33), (12, 20), (12, 13),
                            (13, 15), (14, 17), (14, 20), (14, 16), (15, 20), (15, 21), (15, 22), (15, 23), (16, 33), (16, 23),
                            (16, 32), (17, 31), (18, 19), (20, 21), (20, 24), (20, 25), (21, 22), (22, 27), (22, 28), (22, 23),
                            (23, 32), (23, 29), (25, 26), (29, 30), (30, 31), (31, 32)])

paper3Graph = nx.Graph()
paper3Graph.add_edges_from([(1, 4), (1, 16), (2, 16), (3, 4), (3, 8), (4, 5), (4, 7), (4, 8), (5, 6), (7, 10), (7, 14), (7, 8),
                            (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (14, 16)])

paper4Graph = nx.Graph()
paper4Graph.add_edges_from([(1, 56), (2, 56), (3, 4), (4, 54), (4, 56), (5, 8), (6, 8), (7, 8), (8, 33), (8, 34), (8, 36),
                            (8, 42), (8, 11), (8, 12), (8, 46), (8, 47), (8, 48), (8, 17), (8, 18), (8, 52), (8, 44), (8, 56),
                            (8, 25), (8, 26), (8, 28), (8, 24), (9, 34), (10, 34), (13, 34), (14, 34), (15, 42), (16, 42), (19, 44),
                            (20, 44), (21, 43), (21, 22), (21, 23), (27, 42), (28, 40), (28, 37), (28, 38), (28, 39), (29, 34), (30, 42),
                            (31, 42), (32, 34), (33, 56), (35, 36), (41, 42), (43, 44), (44, 49), (45, 52), (50, 52), (51, 52), (53, 56),
                            (55, 56), (56, 57), (56, 58), (56, 59), (56, 60), (56, 61), (56, 62)])

paper5Graph = nx.Graph()
paper5Graph.add_edges_from([(1, 2), (1, 4), (2, 48), (3, 26), (3, 4), (3, 45), (3, 52), (4, 34), (4, 14), (4, 48), (4, 22),
                            (4, 23), (4, 32), (5, 6), (5, 8), (6, 9), (6, 13), (6, 46), (6, 20), (6, 21), (7, 27), (7, 48), (7, 11),
                            (7, 15), (7, 8), (9, 10), (10, 36), (10, 38), (10, 39), (10, 12), (10, 28), (10, 29), (16, 53), (17, 36),
                            (18, 50), (19, 41), (24, 52), (25, 41), (26, 44), (26, 48), (30, 50), (31, 48), (33, 36), (35, 48),
                            (36, 49), (36, 37), (36, 43), (36, 50), (36, 42), (37, 43), (37, 38), (38, 39), (40, 41), (40, 42),
                            (41, 50), (42, 43), (44, 51), (44, 45), (44, 53), (46, 48), (47, 48), (48, 49), (50, 51), (50, 52), (52, 53)])

paper6Graph = nx.Graph()
paper6Graph.add_edges_from([(1, 2), (2, 3), (2, 5), (2, 7), (3, 4), (3, 5), (5, 6), (6, 7)])

paper7Graph = nx.Graph()
paper7Graph.add_edges_from([(1, 18), (1, 6), (2, 5), (2, 6), (3, 17), (3, 6), (4, 6), (4, 22), (5, 6), (5, 22), (6, 7), (6, 9),
                            (6, 18), (6, 22), (7, 18), (8, 18), (8, 22), (9, 18), (10, 14), (10, 22), (11, 18), (12, 18), (13, 17),
                            (14, 18), (15, 24), (16, 24), (17, 18), (17, 22), (17, 24), (18, 19), (18, 20), (18, 21), (18, 22), (20, 22),
                            (22, 23), (22, 24), (23, 24)])

paper8Graph = nx.Graph()
paper8Graph.add_edges_from([(1, 56), (2, 56), (3, 4), (4, 54), (4, 56), (5, 8), (6, 8), (7, 8), (8, 33), (8, 34), (8, 36),
                            (8, 42), (8, 11), (8, 12), (8, 46), (8, 47), (8, 48), (8, 17), (8, 18), (8, 52), (8, 44), (8, 56),
                            (8, 25), (8, 26), (8, 28), (8, 24), (9, 34), (10, 34), (13, 34), (14, 34), (15, 42), (16, 42), (19, 44),
                            (20, 44), (21, 43), (21, 22), (21, 23), (27, 42), (28, 40), (28, 37), (28, 38), (28, 39), (29, 34),
                            (30, 42), (31, 42), (32, 34), (33, 56), (35, 36), (41, 42), (43, 44), (44, 49), (45, 52), (50, 52),
                            (51, 52), (53, 56), (55, 56), (56, 57), (56, 58), (56, 59), (56, 60), (56, 61), (56, 62)])

paper9Graph = nx.Graph()
paper9Graph.add_edges_from([(1, 2), (1, 2), (1, 4), (1, 14), (1, 15), (1, 15), (1, 8), (1, 8), (1, 8), (2, 8), (2, 8), (2, 8),
                            (2, 9), (2, 10), (2, 11), (2, 12), (2, 14), (2, 15), (2, 15), (3, 8), (5, 10), (6, 9), (7, 15), (8, 9),
                            (8, 9), (8, 9), (8, 10), (8, 10), (8, 12), (8, 15), (9, 10), (9, 10), (9, 12), (9, 15), (13, 14), (14, 15), (15, 16)])

paper10Graph = nx.Graph()
paper10Graph.add_edges_from([(1, 2), (1, 3), (1, 5), (1, 35), (1, 31), (2, 34), (3, 33), (3, 36), (3, 5), (3, 39), (3, 37), (3, 32),
                             (4, 11), (4, 20), (4, 5), (4, 6), (4, 31), (5, 6), (5, 7), (5, 9), (5, 17), (5, 18), (5, 30), (5, 32),
                             (6, 24), (7, 8), (8, 9), (8, 26), (8, 35), (9, 10), (9, 26), (10, 26), (10, 19), (10, 30), (10, 16),
                             (12, 14), (13, 23), (13, 21), (13, 14), (13, 15), (13, 16), (14, 15), (14, 23), (16, 30), (17, 35), (18, 31),
                             (22, 28), (23, 27), (23, 28), (23, 24), (24, 30), (25, 26), (25, 35), (28, 29), (29, 30), (31, 40), (33, 35),
                             (34, 35), (36, 37), (37, 38), (39, 40)])

#Create all the Overlay network graphs
'''print "working on completeGraph"
OGcompleteGraph = OverlayNetwork.OverlayNetworkGraph(completeGraph,1)
print "working on treeGraph"
OGtreeGraph = OverlayNetwork.OverlayNetworkGraph(treeGraph,1)
print "working on treeLoopGraph"
OGtreeLoopGraph = OverlayNetwork.OverlayNetworkGraph(treeLoopGraph,1)
print "working on myGraph"
OGmyGraph = OverlayNetwork.OverlayNetworkGraph(myGraph,1)
print "working on myGraph with MP"
OGmyGraphWithMP = OverlayNetwork.OverlayNetworkGraph(myGraph,1,[1])
print "working on myLoopGraph"
OGmyLoopGraphOneMP= OverlayNetwork.OverlayNetworkGraph(myLoopGraph,1)
print "working on myGraph with 2 MPs"
OGmyGraphTwoMP = OverlayNetwork.OverlayNetworkGraph(myGraph,2)
print "working on myLoopGraph 2 MPs"
OGmyLoopGraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(myLoopGraph,2)
print "working on myGraph with 3 MPs"
OGmyGraphThreeMP = OverlayNetwork.OverlayNetworkGraph(myGraph,3)
print "working on myLoopGraph 3 MPs"
OGmyLoopGraphThreeMPs = OverlayNetwork.OverlayNetworkGraph(myLoopGraph,3)
print "working on OGtestGraph1 one set MP"
OGtestGraph1 = OverlayNetwork.OverlayNetworkGraph(testGraph1,1,[3])
print "working on cycleGraph one MP"
OGCycleGraphsingleMP = OverlayNetwork.OverlayNetworkGraph(cycleGraph,1)
print "working on cycleGraph two MPs"
OGCycleGraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(cycleGraph,2)
print "working on cycleGraph three MPs"
OGCycleGraphThreeMPs = OverlayNetwork.OverlayNetworkGraph(cycleGraph,3)
print "working on cycleStringGraph one MP"
OGCycleStringGraphsingleMP = OverlayNetwork.OverlayNetworkGraph(cycleStringGraph,1)
print "working on cycleStringGraph two MPs"
OGCycleStringGraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(cycleStringGraph,2)'''''


####### Tests for get topologies for  all the paper graphs single and two MPs ####
'''print "working on paper0Graph single MP"
OGpaper0GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper0Graph, 1)
print "working on paper1Graph two MPs"
OGpaper0GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper0Graph, 2)
print "working on paper1Graph single MP"
OGpaper1GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper1Graph, 1)
print "working on paper1Graph two MPs"
OGpaper1GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper1Graph, 2)
print "working on paper2Graph single MP"
OGpaper2GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper2Graph, 1)
print "working on paper2Graph two MPs"
OGpaper2GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper2Graph, 2)
print "working on paper3Graph single MP"
OGpaper3GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper3Graph, 1)
print "working on paper3Graph two MPs"
OGpaper3GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper3Graph, 2)
print "working on paper4Graph single MP"
OGpaper4GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper4Graph, 1)
print "working on paper4Graph two MPs"
OGpaper4GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper4Graph, 2)
print "working on paper5Graph single MP"
OGpaper5GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper5Graph, 1)
print "working on paper5Graph two MPs"
OGpaper5GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper5Graph, 2)
print "working on paper6Graph single MP"
OGpaper6GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper6Graph, 1)
print "working on paper6Graph two MPs"
OGpaper6GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper6Graph, 2)
print "working on paper7Graph single MP"
OGpaper7GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper7Graph, 1)
print "working on paper7Graph two MPs"
OGpaper7GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper7Graph, 2)
print "working on paper8Graph single MP"
OGpaper8GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper8Graph, 1)
print "working on paper8Graph two MPs"
OGpaper8GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper8Graph, 2)
print "working on paper9Graph single MP"
OGpaper9GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper9Graph, 1)
print "working on paper9Graph two MPs"
OGpaper9GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper9Graph, 2)
print "working on paper10Graph single MP"
OGpaper10GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper10Graph, 1)
print "working on paper10Graph two MPs"
OGpaper10GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper10Graph, 2)'''

######Tests for topology 1 and 2 for the impact of MPs ####
'''print "working on paper1Graph single MP"
OGpaper1GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper1Graph, 1)
print "working on paper1Graph two MPs"
OGpaper1GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper1Graph, 2)
print "working on paper1Graph three MP"
OGpaper1GraphThreeMPs = OverlayNetwork.OverlayNetworkGraph(paper1Graph, 3)
print "working on paper1Graph four MPs"
OGpaper1GraphFourMPs = OverlayNetwork.OverlayNetworkGraph(paper1Graph, 4)
print "working on paper1Graph five MP"
OGpaper1GraphFiveMPs = OverlayNetwork.OverlayNetworkGraph(paper1Graph, 5)
print "working on paper1Graph six MPs"
OGpaper1GraphSixMPs = OverlayNetwork.OverlayNetworkGraph(paper1Graph, 6)'''
print "working on paper2Graph single MP"
OGpaper2GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper2Graph, 1)
'''print "working on paper2Graph two MPs"
OGpaper2GraphTwoMPs = OverlayNetwork.OverlayNetworkGraph(paper2Graph, 2)
print "working on paper2Graph three MPs"
OGpaper2GraphThreeMPs = OverlayNetwork.OverlayNetworkGraph(paper2Graph, 3)
print "working on paper2Graph four MP"
OGpaper2GraphFourMPs = OverlayNetwork.OverlayNetworkGraph(paper2Graph, 4)
print "working on paper2Graph five MP"
OGpaper2GraphFiveMPs = OverlayNetwork.OverlayNetworkGraph(paper2Graph, 5)
print "working on paper2Graph six MPs"
OGpaper2GraphSixMPs = OverlayNetwork.OverlayNetworkGraph(paper2Graph, 6)'''

#####Test to find worst MPs for topo 1 and topo 2 ####
'''for i in xrange(25):
    print "working on paper1Graph ",i+1," MPs"
    OGpaper1GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper1Graph,1,[i+1])

for i in xrange(33):
    print "working on paper2Graph ",i+1," MPs"
    OGpaper2GraphSingleMPs = OverlayNetwork.OverlayNetworkGraph(paper2Graph,1,[i+1])'''