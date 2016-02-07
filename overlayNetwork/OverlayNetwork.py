__author__ = 'ubuntu'

import networkx as nx
import Queue
import time

''' The file purpose is to build the overlay network for every given topology and number of measurement points'''


def getSortedEdges(edgesList):
    """
    Get list of edges, and return the edges list with smaller index first.
    :param edgesList: List of edges.
    :return: Edges list with smaller index first.
    """

    # Traverse the list and if the first index is smaller than the second, replace them.
    for edge in edgesList:
        if (edge[1] < edge[0]):
            i = edgesList.index(edge)
            edgesList[i] = (edge[1],edge[0])
    return edgesList


def combineTwoList (firstList, secondList):
    """
    Get two lists and combine them without duplications, return the result.
    :param firstList: First list.
    :param secondList: Second list.
    :return: Combined list with not duplications.
    """

    return list(set(firstList + secondList))

def getAdjacentEdges(graph, node):
    """
    Return all the edges (smaller index first connected to the given node.
    :param graph: Given Graph
    :param node: Given node.
    :return: All the edges (smaller index, bigger index) connected to the given node.
    """

    adjacentEdges = []
    for neighbor in sorted(graph.neighbors(node)):
        adjacentEdges += getSortedEdges([(node, neighbor)])

    return adjacentEdges

def getAllEdgesBetweenGivenNodes(graph,nodes):
    '''return all the edges including the data that are between the nodes in the given list'''
    edgesToReturn = []
    for edge in getSortedEdges(graph.edges()):
        #if both source and destination are in nodes then add the edge to the edges to return
        if ((edge[0] in nodes) and  (edge[1]  in nodes)):
            edgesToReturn.append(edge)

    return edgesToReturn

def buildOverlayNetworkSingleMP(graph, MP,depths):
    '''Given network with known MP
    first set params - depths, closest MP, source and destination (for every edge)
    build the overlay network by setting the type for every edge '''

    #create an empty dictionary of subtreeSizes - for balancing purpose
    subGraphSizes = {}

    #Save a copy of the edges and nodes to make sure they are all handled
    edgesCopy = getSortedEdges(graph.edges())
    nodesCopy = sorted(graph.nodes())

    #MP has to be handled once only so remove it
    nodesCopy.remove(MP)

     #Set the params for the overlay network
    setParamsForMPedOverlayNetwork(graph,[MP])

    #Set the weight for this graph edges
    setWeight(graph)

    for edge in graph.edges():
        depths[graph[edge[0]][edge[1]]['depth']] +=1

    #Save all edges next to the MP, they will be the indexes of subgraph
    for edge in getAdjacentEdges(graph,MP):
        #Should not be handled no more so remove edge
        edgesCopy.remove(edge)

        #They will be consecutive for sure - set type to 0
        graph[edge[0]][edge[1]]['Type'] = 0

        #Get the adjacent node
        otherNode = getAdjacentVertex(MP, edge)
        #Set the number of in edges to be 1 and the subgraph index to be the current node index
        graph.node[otherNode]['numOfInEdges'] = 1
        graph.node[otherNode]['subGraphIndex'] = otherNode
        #Set the subtree size of this index to be initialized to this edge value
        subGraphSizes[otherNode] = graph[edge[0]][edge[1]]['weight']

    #Done handling MP's adjacent edges which are special case

    #Now the depth of nodes is 1
    currentDepth = 1
    #Handle all the nodes (if you handle all the nodes adjacent edges you will handle all edges as well
    while (0 != len(nodesCopy)):

        #Create a list of nodes with current depth (were not handled yet so can be taken from nodesCopy)
        nodesInCurrDepth = []
        for node in nodesCopy[:]:
            if (graph.node[node]['depth'] == currentDepth):
               nodesInCurrDepth.append(node)
               nodesCopy.remove(node) #dont need to be handled no more if will be handled as part of nodes with current depth

        #Handle all nodes in current depth
        while (0 != len(nodesInCurrDepth)):

            currNode = 0
            currMinimalSubGraphSize = 1000 #Set a large number because we want to find the minimal subgraph to increase

            #Find the next node to handle (the node that related to subgraph with minimal size)
            for node in nodesInCurrDepth:
                #If this node subgraph size is smaller then first handle this node- save the current node and minimal subgraph size
                if (subGraphSizes[graph.node[node]['subGraphIndex']] < currMinimalSubGraphSize):
                    currMinimalSubGraphSize = subGraphSizes[graph.node[node]['subGraphIndex']]
                    currNode = node

            #Get all the edges next to current node that where not handled yet
            #which means get the intersection of neighbors with edge copy
            unhandledNeighborEdges = list(set(getAdjacentEdges(graph,currNode)) & set(getSortedEdges(edgesCopy)))

            #If the node still have neighbors edges that were not handled
            if (0 != len(unhandledNeighborEdges)):

                #Save dummy edge because need to find actual edge to work on
                currEdge = (0,0)
                currentMaximalEdgeSize = -1 #Set the edge size to be low because we look for maximal size

                #Get the current edge to work on- the edge with max weight from the unhandledNeighborEdges list
                for edge in (unhandledNeighborEdges):
                    #If this edge is heavier than others, set it to be the current edge
                    if (graph[edge[0]][edge[1]]['weight'] > currentMaximalEdgeSize):
                        currEdge = (edge[0],edge[1])
                        currentMaximalEdgeSize = graph[edge[0]][edge[1]]['weight']

                edgesCopy.remove(currEdge ) #Remove this edge so will be handled only once

                #Handle current edge , currNode and node in the other side

                #Get the node in the other side of this edge
                otherNode = getAdjacentVertex(currNode, currEdge)

                #If the node has no edges that entered to it yet (which mean it has to be consecutive edge)
                #Set its sub graph index,type
                #Also, add its weight to the subtree sizes
                if (0 == graph.node[otherNode]['numOfInEdges']):
                    graph[currEdge[0]][currEdge[1]]['Type'] = 0
                    graph.node[otherNode]['subGraphIndex'] = graph.node[currNode]['subGraphIndex']
                    subGraphSizes[graph.node[currNode]['subGraphIndex']] += graph[currEdge[0]][currEdge[1]]['weight']

                else: #If this node was already reached, set type to be dashed and increase subgraph by the value
                      #Here it is a delicate point, if it has weight 0 , you have to add weight as 0, otherwise add 1
                      #Because if it was 0, it means that its weight was already taken before (when added the edge
                      #that is the parent of current subtree). Otherwise, the size can be 1 or bigger than 1, but
                      #if bigger than 1, should only take 1 because this is not consecutive line
                      #Mo meed tp set tje node subgraph because it is already related to other subgraph
                    graph[currEdge[0]][currEdge[1]]['Type'] = 1
                    subGraphSizes[graph.node[currNode]['subGraphIndex']] += min(graph[currEdge[0]][currEdge[1]]['weight'],1)

                #Now after set the subgraph sizes were set, the type of the edge was set and if required also the
                #SubGraph index of each node was set need to set few more params

                #Increase the number of in edges for other node, number of out edges for currNode and src and dst for edge
                graph[currEdge[0]][currEdge[1]]['src'] = currNode
                graph[currEdge[0]][currEdge[1]]['dst'] = otherNode
                graph.node[otherNode]['numOfInEdges'] += 1
                graph.node[currNode]['numOfOutEdges'] += 1


            else: #If all its neighbors where handled, remove the node
                nodesInCurrDepth.remove(currNode)

        #Handled all nodes in current depth go to deeper nodes
        currentDepth += 1

    #print "subGraph sizes" , subGraphSizes
    return  currentDepth
    #Now all nodes and edges was set, can add here balancing for number of out edges per node as long as the depth
    #won't be damaged. or other improvements

def setWeight(graph):
    '''Set the weight to all the edges, edges assumed to contain the depth already
    The weight represent the value of the edge only if it will be added to the graph as consecutive edge!
    when we will check the edge, and its value is bigger than 1, we will add this value only if is consecutive
    edge, otherwise the value will be added as 1 or 0 (because there is no distribution to the subtree edges in this case
    1 if its weight is 1 or bigger, or 0 if its weight is 0'''

    #Get all the edges in the graph to make sure they all will be handled and sort them by depth
    #Notice that they are returned as small id, big id, data
    edgesToHandleNoData = []
    for edge in sorted(graph.edges(data = True), key = lambda  x:x[2]['depth']):
        edgesToHandleNoData += getSortedEdges([(edge[0],edge[1])])

    #Work until all the edges will have desired value (which means are still in the list
    while (0 < (len(edgesToHandleNoData))):
        #Get the first edge in the list (evey time it will be the edge with lowest depth in the list
        currEdge = edgesToHandleNoData[0]

        #Get the dest and source of this edge
        currDestNode = graph[currEdge[0]][currEdge[1]]['dst']
        currSrcNode = graph[currEdge[0]][currEdge[1]]['src']

        #Check if the dest node is a subtree parent
        #To check this,copy he graph and remove the current edge and all the edges with the same depth in the graph
        # and same dest node (which are in a "race" of who will be consecutive to this node and who will be dashed)
        #Then run a bfs_tree from the dest node, if the source node is in this bfs tree there is a loop in the graph
        #and the weight of the edge is and all the other edges in the same race condition is 1
        #otherwise it has to be handled, the weight of these edges will be the 1 + the size of their subtree
        #Their subtree edges weight will be 0 because it will be included in the previous edge weight already

        #Save all the edges with the same depth and same dest node (as the currEdge)- these edges will have the same weight
        edgesWithSameWeightAnDest = []
        for edge in edgesToHandleNoData[:]:
            if ((graph[edge[0]][edge[1]]['dst'] == currDestNode) and
                        (graph[currEdge[0]][currEdge[1]]['depth']) == (graph[edge[0]][edge[1]]['depth'])):
                edgesWithSameWeightAnDest.append(edge)
                edgesToHandleNoData.remove(edge) #These edges will have weight in the edge
                                                              # of this loop so no need to handle them no more

        #Copy the graph and remove all the edges with the same weight
        copyGraph = (graph.copy())
        for edge in edgesWithSameWeightAnDest:
            copyGraph.remove_edge(edge[0],edge[1])

        #check if there is a loop in the dest subtree by bfs the dest without the edges removed (we are checking for deeper subtree with dest as a MP)
        #run a bfs tree of the copyGraph from the currDest node and if the current source node is
        #reachable it means there is another way to reach it and that current dest node is not a parent
        #of a subtree - so if this condition will be true the value should be 1
        maybeSubtreeGraph = nx.bfs_tree(copyGraph, currDestNode)
        weightToSet = graph[currEdge[0]][currEdge[1]]['weight'] #save the current weight of the edge
        if (currSrcNode not in maybeSubtreeGraph):
            #This case if if this is  subtree parent, all the edges in the subtree need to have value 0 and
            # the current edge have weight as the number of all the edge
            subtreeEdges = getAllEdgesBetweenGivenNodes(graph,maybeSubtreeGraph.nodes())
            #Set the value to be the number of edges in the subtree
            for edge in subtreeEdges:
                weightToSet += graph[edge[0]][edge[1]]['weight']
                #remove the edge
                edgesToHandleNoData.remove(edge)
                graph[edge[0]][edge[1]]['weight'] = 0

        for edge in edgesWithSameWeightAnDest:
            graph[edge[0]][edge[1]]['weight'] = weightToSet

def setParamsForMPedOverlayNetwork(graph,MPs):
    '''Set the parameters of depth, closest MP and also the src and dest as a preparation to building the ON'''
    #Get nominee graph and set its params
    tempNomineeGraph = NomineeGraph(MPs, graph)

    #Copy the parameter for the nodes
    for nodeID in tempNomineeGraph.graph.nodes():
         graph.node[nodeID]['closestMPs'] = tempNomineeGraph.graph.node[nodeID]['closestMPs']
         graph.node[nodeID]['depth'] = tempNomineeGraph.graph.node[nodeID]['depth']

    #Copy the parameter for the edges
    for edge in tempNomineeGraph.graph.edges():
        graph[edge[0]][edge[1]]['depth'] = tempNomineeGraph.graph[edge[0]][edge[1]]['depth']
        graph[edge[0]][edge[1]]['closestMPs'] = tempNomineeGraph.graph[edge[0]][edge[1]]['closestMPs']
        graph[edge[0]][edge[1]]['dst'] = tempNomineeGraph.graph[edge[0]][edge[1]]['dst']
        graph[edge[0]][edge[1]]['src'] = tempNomineeGraph.graph[edge[0]][edge[1]]['src']


def getAdjacentVertex(n , e):
    '''Given edge and connected to this edge in a graph, it returns the other node connected to the edge'''
    if (e[0] == n):
        return e[1]
    else:
        return e[0]

class NomineeGraph(object):
    '''This class contains all the data for a nominee graph'''

    def __init__ (self, MPs, graph):
        '''Init all the paramsGiven graph and MPs'''
        #save all the MPs for the given graph
        self.MPs = sorted(MPs)
        #Create a new empty graph
        self.graph = nx.Graph()
        #Initialize the max depth to be 1
        self.MaxDepth = 1
        #Initialize array of depths
        self.depths = [0]
        #Add all nodes from the original graph with depth 0 and empty list of closest MPs
        for node in sorted(graph.nodes()):
            self.graph.add_node(node, depth = 0, closestMPs = [])

        #Add all edges with depth 0, src, dst (assumed by default to be by order) and empty list of closest MPs
        for src,dst in getSortedEdges(graph.edges()):
            #By default the edge is assumed to be sorted as it is directed
            #this is not really one direction graph but we do want to know which node is deep and which is shallow
            self.graph.add_edge(src, dst, depth = 0, src = src, dst = dst, closestMPs = [])

        #Set the depth for nodes and edges
        self.setDepthSourceAndDestination()

        #Now we have a nominee graph when we know all the params for a nominee,
        #If we want to peek a MP, will will look for the best MP by using the params when considering different
        #MPs for the same graph and check for nominees

    def setDepthSourceAndDestination(self):
        '''Set the depth for all the edges and all the nodes in the graph and which MPs are the closest
        also set the source and the dest of the graph'''

        #Create Queue
        q = Queue.Queue(maxsize = len(self.graph)) #To handle the element by order
        nextLevelQ = Queue.Queue(maxsize = len(self.graph)) #To handle all the nodes that need to have the next depth

        #Save a copy of the edges and nodes to make sure they are all handled
        edgesCopy = getSortedEdges(self.graph.edges())
        nodesCopy = sorted(self.graph.nodes())
        currentDepth = 0 #The depth of the MPs is always 0
        #remove all MPs from nodes and add them to q (the first nodes to be handled)
        for r in sorted(self.MPs):
            nodesCopy.remove(r)
            q.put(r)

        #Run until all the edges are handles
        while (len(edgesCopy) != 0):
            #While there are still nodes in this level (handle nodes by levels)
            while not(q.empty()):
                currNode = q.get() #Get current node
                # Special case where we handle the MPs- set them to be the closest to themselves
                if (0 == currentDepth): #if we are still working with the MPs, they are the closest
                    (self.graph.node[currNode]['closestMPs']).append(currNode)

                self.graph.node[currNode]['depth'] = currentDepth #Set the depth
                adjacentEdges = getAdjacentEdges(self.graph,currNode) #get all the edges connected to this node
                for edge in adjacentEdges: #Run on all the edges connected to this node'

                    if (edge in edgesCopy): #only for edges that were not processed yet (if not in edgesCopy, has weight already)
                        edgesCopy.remove(edge) # this edge is now processed

                        #Set the closest MPs
                        self.graph[edge[0]][edge[1]]['closestMPs'] = \
                            combineTwoList(self.graph[edge[0]][edge[1]]['closestMPs'], self.graph.node[currNode]['closestMPs'])

                        #Set the depth of this edge to be currDepth +1
                        self.graph[edge[0]][edge[1]]['depth'] = currentDepth + 1
                        self.depths[currentDepth] += 1 #new edge for depth

                        #Set the source and the dest (they are opposite from default so need to be switched)
                        if (currNode == edge[1]):
                            self.graph[edge[0]][edge[1]]['src'] = edge[1]
                            self.graph[edge[0]][edge[1]]['dst'] = edge[0]

                        otherNode = getAdjacentVertex(currNode,edge) #get the vertex in other side of the edge
                        if (otherNode in nodesCopy): #process the node only if wasn't processed yet
                            nodesCopy.remove(otherNode) #remove the node so it wont be processed again
                            #Set the closest MPs
                            self.graph.node[otherNode]['closestMPs'] = \
                                combineTwoList(self.graph.node[otherNode]['closestMPs'], self.graph.node[currNode]['closestMPs'])
                            self.graph.node[otherNode]['depth'] = currentDepth + 1 #set the depth for this node
                            nextLevelQ.put(otherNode) #Put the node in the next level queue so it will be handled with all the node with same depth

                        #if the node was processed already, but its depth is the same depth from current MP maybe need to update the closest MPs
                        elif (self.graph.node[otherNode]['depth'] == (currentDepth + 1)):
                            #Set the closest MPs (no duplications)
                            self.graph.node[otherNode]['closestMPs'] = \
                                combineTwoList(self.graph.node[otherNode]['closestMPs'], self.graph.node[currNode]['closestMPs'])

                    #if the edge was processed already, but its depth is the same depth from current MP maybe need to update the closest MPs
                    elif (self.graph[edge[0]][edge[1]]['depth'] == (currentDepth + 1)):
                        #Set the closest MPs
                        self.graph[edge[0]][edge[1]]['closestMPs'] = \
                            combineTwoList(self.graph[edge[0]][edge[1]]['closestMPs'], self.graph.node[currNode]['closestMPs'])

                #Handled all adjacent edges of current node

            #Handled all edges of this depth

            currentDepth += 1 #the depth is now bigger by one
            self.depths.append(0) # add location in depths for new depth

            #empty the next level q to q so it will be handled in the next level
            while (not nextLevelQ.empty()):
                q.put(nextLevelQ.get())

        #Handled all edges

        #Save the maximum depth
        self.MaxDepth = currentDepth

class OverlayNetworkGraph(object):
    '''This class contains all the data for an overlay network graph'''

    def __init__ (self, graph, k, MPs = None):
        '''Init all the params for a given graph and k as number of MPs'''

        #Save how many MPs
        self.numOfMPs = k



        #Create a new empty graph
        self.graph = nx.Graph()

        #Add all nodes with the following params:
        #Depth - how deep is this node, set to be 0
        #Sub Graph Index - the index of sub graph the node related to, set to 0
        #Num Of In Edges - How many edges actually enter this node, set to 0
        #Num Of Out Edges - How many edges are pointed out of this node, how many sons this node have, set to 0

        for node in sorted(graph.nodes()):
            self.graph.add_node(node, depth = 0, subGraphIndex = 0, numOfInEdges = 0,
                                numOfOutEdges = 0)

        #Add all edges with the following params:
        #Depth - how deep is this edge ,set to be 0
        #Weight - How many edges will be added if this edge will be added as consecutive edge. set to be 1 as default
        #Src - The source node for this edge, set to be the first edge at the beginning
        #Dst - The dest node for this edge, set to be the second node at the beginning
        #Type - The type of this link, 0 for continuous, 1 for dashes  , initialized to be 2 (unknown)
        #closestMP - set the list of closest MPs of this edge to be none
        for src,dst in sorted(graph.edges()):
            #By default the edge is assumed to be sorted as it is directed
            #this is not really one direction graph but we do want to know which node is deep and which is shallow
            self.graph.add_edge(src, dst, depth = 0 ,  weight = 1 , src = src, dst = dst, Type = 2 , closestMP = None)

        results = []
        resultsSum = 0
        numberOfTestsToRun = 1
        for num in xrange(numberOfTestsToRun):
            #Set the MPs
            if MPs is None:
                self.MPs = []
            else:
                self.MPs = sorted(MPs)

            startTime = time.time()

            #Find the best MPs for this graph
            self.findKMPs(k)

            #Prepare for building the overlay network by setting depth and weight params
            setParamsForMPedOverlayNetwork(self.graph,self.MPs)

            #Build the overlay network
            self.buildOverlayNetworkKMPs()

            #Set the info for the rules
            self.setParentAndDistributionPerNode()

            CurrentBuildingTime = time.time() - startTime
            results.append(CurrentBuildingTime)
            resultsSum += CurrentBuildingTime

        #print "Building times:", results
        print "avg building time was"
        print("%.2f" % (resultsSum/numberOfTestsToRun*1000))

        #Print the info
        self.printAllInfoForOverlayGraph()

    def findKMPs(self, k):
        '''find the optimal MPs, the priority for best MPs is:
        first by lowest maximal depth-  the maximal depth should be minimal
        second by lowest maximum number of edges in this depth
        then by maximal number of neighbors'''

        #Work until we found the desired number of MPs
        while (self.numOfMPs != len(self.MPs)):
            #Set all the values that we lok to be minimum to be high and maximum to be low
            currMaxDepth = 1000 #The maximum depth for nominee
            currNumOfEdgesMaxDepth = 1000 # How many edges in maximum depth for nominee
            currNeighbors = 0 #How many neighbors the edge has
            currentMP = 0 #The current MP

            #Run over all the nodes that are not in the MP already and take the best one (greedy algorithm)
            for node in list(set(self.graph.nodes())-set(self.MPs)):
                #Set the nominee graph with all relevant params (with current MP plus one more MP)
                tempNomineeGraph = NomineeGraph(self.MPs + [node], self.graph)
                #Set all the params of the nominee Graph
                nodeMaxDepth = tempNomineeGraph.MaxDepth

                nodeNumOfEdgesMaxDepth = tempNomineeGraph.depths[nodeMaxDepth-1]
                nodeNeighbors = len(nx.neighbors(tempNomineeGraph.graph,node))
                #Check on params by order, if node is better  as MP need to set it as new MP
                #Pay attention that we want more neighbors and not less so the order there is the opposite
                if ((currMaxDepth,currNumOfEdgesMaxDepth,nodeNeighbors) > (nodeMaxDepth,nodeNumOfEdgesMaxDepth,currNeighbors)):
                    #set the params
                    currMaxDepth,currNumOfEdgesMaxDepth,currNeighbors = nodeMaxDepth,nodeNumOfEdgesMaxDepth,nodeNeighbors
                    #set the current MP
                    currentMP = node

            self.MPs.append(currentMP)


    def buildOverlayNetworkKMPs(self):
        '''This function split the nodes between the MPs, then builds for every MP its own Overlay graph
        Then, it merge all graphs to one graph and make sure that only one edge is consecutive for every edge'''

        #Create an empty dictionary of sub overlay graphs that will contain Overlay Graph and empty dictionary of graphs
        subOverlayGraphs = {}
        subGraphs = {}
        subGraphSizes = {}
        #Set an empty graph for every graph subGraph
        for MP in sorted(self.MPs):
            subGraphs[MP] = nx.Graph()
            subGraphSizes[MP] = 0

        #Split the edges and nodesbetween the graphs, sort by how many closest MPs there are,
        #First divide the edge than has only 1 closest MP so we can know for sure where it should go
        #Then try to balance by adding the edge to the lowest size subgraph
        for edge in sorted(self.graph.edges(data = True), key = lambda  x:len(x[2]['closestMPs'])):
            #Get the closest MPs
            closestMPs = edge[2]['closestMPs']

           #Find the lowest size subgraph from the subgraphs of closest MPs to add the edge to
            currMinimalSize = 1000
            for MP in closestMPs:
                if (subGraphSizes[MP] < currMinimalSize):
                    closestMP = MP
                    currMinimalSize = subGraphSizes[MP]

            #Add the edge and nodes to the MP's subGraph
            subGraphSizes[closestMP] +=1
            #Add source node and dest node
            subGraphs[closestMP].add_nodes_from([(edge[0],self.graph.node[edge[0]]),(edge[1],self.graph.node[edge[1]])])
            subGraphs[closestMP].add_edges_from([edge])

        #Now we have all the edges divided to graphs

        #Calculate the overlay graph as it had a single MP and set the type to all the egdes in the graph
        #In addition the src and dest might have changed so need tobe updated
        self.Depths = [0,0,0,0,0,0,0,0,0,0,0,0]
        for MP in sorted(self.MPs):
            maxDepthForMP = buildOverlayNetworkSingleMP(subGraphs[MP],MP,self.Depths)

            for edge in (subGraphs[MP]).edges(data = True):
                self.graph[edge[0]][edge[1]]['Type'] = edge[2]['Type']
                self.graph[edge[0]][edge[1]]['src'] = edge[2]['src']
                self.graph[edge[0]][edge[1]]['dst'] = edge[2]['dst']

        #Validate that every node has only one consecutive edge (if the node was related to several suboverlay graphs
        # it will have more and that should be fixed)
        for node in sorted(self.graph.nodes()):
            consecutiveAdjacentEdgesCurrentDepth = 1000
            currConsecutiveAdjacentEdge = None

            #Save if the node is a MP or not
            if (node in self.MPs):
                isMP = True
            else:
                isMP = False

            #Run over all the edges
            for edge in sorted(getAdjacentEdges(self.graph,node)):
                #Check if consecutive edge directed to current node
                if ((self.graph[edge[0]][edge[1]]['Type'] == 0) and (node == self.graph[edge[0]][edge[1]]['dst'])):
                    #if the node is a MP, no consecutive edges enter into this node so set the edge to type 1 (dashed)
                    if (isMP):
                        self.graph[edge[0]][edge[1]]['Type'] = 1

                    #else ,If edge has lower depth and dest node is not the MP
                    else:
                        if (self.graph[edge[0]][edge[1]]['depth'] < consecutiveAdjacentEdgesCurrentDepth):
                            #Set the type of previous edge to be 1, dashed, if the edge exist
                            if (None != currConsecutiveAdjacentEdge):
                                self.graph[currConsecutiveAdjacentEdge[0]][currConsecutiveAdjacentEdge[1]]['Type'] = 1
                            #Set new lowest depth and currConecutive edge to be current edge
                            consecutiveAdjacentEdgesCurrentDepth = self.graph[edge[0]][edge[1]]['depth']
                            currConsecutiveAdjacentEdge = edge

                        #If it is not deeper, set its type to be 1
                        else:
                            self.graph[edge[0]][edge[1]]['Type'] = 1



    def setParentAndDistributionPerNode(self):
        '''After the overlay graph was built, we can traverse the edges and set the parent and distribution nodes
        for every node in the graph'''

        #parent node - The node which is the parent of this node in the overlay graph (MPs parent will be itself)
        #Distribution nodes - list of nodes to distribute the packet to, on distribution command , set to empty list

        #Set parent switch as empty dictionary
        self.parentSwitch = {}

        #set distribution switches as dictionary of empty lists
        self.distributionSwitches = {}
        for node in self.graph.nodes():
            self.distributionSwitches[node] = []

        #Set the parent switch of all the MPs to be themsevles
        for MP in self.MPs:
            self.parentSwitch[MP] = MP

        #Get the info from all the edges
        for edge in self.graph.edges():
            #If it is a consecutive edge, set the parent node of the dest node to be the source node
            if (self.graph[edge[0]][edge[1]]['Type'] == 0):
                self.parentSwitch[self.graph[edge[0]][edge[1]]['dst']] = self.graph[edge[0]][edge[1]]['src']
            #Set the dest node to be distribution port of source node
            self.distributionSwitches[self.graph[edge[0]][edge[1]]['src']].append(self.graph[edge[0]][edge[1]]['dst'])

    def printAllInfoForOverlayGraph(self):
        '''print all the information for the given nominee'''

        '''print "---MPs---"
        print self.MPs
        print "---nodes---"
        for node in self.graph.nodes(data=True):
            print node
        print "---edges---"
        for edge in self.graph.edges(data=True):
            print edge'''
        print "MPs", self.MPs

        self.Depths[0] = len(self.MPs)

        maxDepth = 0
        while (self.Depths[maxDepth] != 0):
            maxDepth+=1
        print "Depths", self.Depths
        print "maxDepth", maxDepth
        print "---parent and distribution nodes---"
        for node in self.graph.nodes():
            print "node", node, "- parent node is:", self.parentSwitch[node], "and distribution nodes are", self.distributionSwitches[node]