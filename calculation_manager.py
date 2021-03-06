#database of ref points and their respective db and freqs to each access point
#database of access points and db and frequencies
#the floor and building you're on (buildingname-floor#)
#floorplan map and location of each AP and ref point
#take ref points and model out a graph using adjacent ref points
#NEED REF POINT AT EACH CORNER/INTERSECTION
#Find nearest ref points to location
#go through points in a line and find most accurate points in the adjacent ref points
#that's their location
#use map to get dist between points to model as graph
#shortest dist is easy
#Ref points need unique ID's

from math import *
from queue import *

curLocation = False
tries = 0

class RefPoint:
    def __init__(self, ID, signalList, pos):
        self.ID = ID #Random unique ID
        self.signalList = signalList #Contains AP db's and freqs
        self.pos = pos #XY pos on map, go by 0-1 scale

    def getError(self, locList):
        tot = 0
        n = 0
        #sig is mac address
        #print(locList)
        #print(self.signalList)
        errs = []
        for sig in set(locList.keys()) | set(self.signalList.keys()):
            if sig not in self.signalList.keys():
                errs.append(abs(110-locList[sig]))
            elif sig not in locList.keys():
                errs.append(abs(110-self.signalList[sig]))
            else:
                errs.append(abs(self.signalList[sig]-locList[sig]))
            n += 1
        errs.sort()
        tot = sum(errs[:3])
        return tot/3



#rp = ref point list
#fp = floor plan
#sc = scale of pixels in a meter
#pairs = list of all ref point ID pairs that make an edge
#rlocs = list of all the positions of rps
def Initialize(rp, fp, sc, p):
    global floorPlan, scale, refPoints, curLocation, graph, closestNode, refCount, pairs, edges, tries, pairToIndex
    floorPlan = fp
    scale = sc #How many pixels are in a meter
    pairs = p
    curLocation = False
    tries = 0
    #List of all  points (~75)?
    #each ref point contains 3 things: an ID, a signal list to all AP's, and a location scaled from 0 to 1 (ignore pixel coords currently there)
    refPoints = []
    refCount = len(rp)
    w = 0
    pairToIndex = {}
    for k in rp.keys():
        aps = []

        if 'aps' in rp[k]:

            for a in rp[k]["aps"].keys():
                aps.append([abs(rp[k]["aps"][a]), a])
                if aps[-1][0] == 1:
                    aps[-1][0] = 120
            aps.sort()
            apd = {}
            for _ in range(min(5, len(aps))):
                apd[aps[_][1]] = aps[_][0]
            refPoints.append(RefPoint(w, apd, rp[k]["location"]))
            pairToIndex[k] = w
            w += 1

    #Make edges list
    edges = []
    for i in range(len(pairs)):
        #print(i, pairs[i])

        #if pairs[i] != '0|164279986487971070|8906485671191552':

        if pairs[i][0] in pairToIndex and pairs[i][1] in pairToIndex:
            edges.append((pairToIndex[pairs[i][0]], pairToIndex[pairs[i][1]]))
        

    # address:[(address, dist), (address, dist)]
    # Ref points and what each ref point is connected to
    # [N:[nodes], M:[nodes]]
    graph = []
    for i in range(refCount):
        graph.append([])
    for pair in edges:
        a = pair[0]
        b = pair[1]
        dist = ((refPoints[a].pos[0]-refPoints[b].pos[0])**2+(refPoints[a].pos[1]-refPoints[b].pos[1])**2)**0.5
        graph[a].append((b, dist))
        graph[b].append((a, dist))


    
#Mac Address:(Db, f)
#This is your current location signals to each AP
#locSigs = {1:(1, 1), 2:(3, 5), 4:(9, 2)}

def findLocation(abd):
    global curLocation, tries, closestNode, pointA, pointB

    prevLocation = curLocation
    aps = []
    for a in abd.keys():
        aps.append([abs(abd[a]), a])
        if abd[a] == 1:
            aps[-1][0] = 120
    aps.sort()
    locSigs = {}
    for _ in range(min(5, len(aps))):
        locSigs[aps[_][1]] = aps[_][0]
##############
    temp = []

    for e in edges:
        a = refPoints[e[0]]
        b = refPoints[e[1]]
        tot = a.getError(locSigs)+b.getError(locSigs)
        temp.append((tot, a.ID, b.ID, a.pos, b.pos))

    topNodeIDs = min(temp)
    #print(topNodeIDs)
    pointA = topNodeIDs[1]
    pointB = topNodeIDs[2]
    totError = topNodeIDs[0]+2
    x = topNodeIDs[3]
    y = topNodeIDs[4]
    curLocation = (x[0] + (y[0]-x[0])*((refPoints[pointA].getError(locSigs)+1)/totError), x[1] + (y[1]-x[1])*((refPoints[pointA].getError(locSigs)+1)/totError))
    closestNode = (x, topNodeIDs[1])
##############    
##    nodeBreadth = 2 #Number of nodes whose paths are being checked
##
##    #Gets nodes whose avg error / AP signal are lowest
##    temp = []
##    for r in refPoints:
##        temp.append((r.getError(locSigs), r.ID, r.pos))
##    temp.sort()
##    topNodeIDs = temp[:nodeBreadth]
##
##    pointA = topNodeIDs[0][2]
##    pointB = topNodeIDs[1][2]
##    totError = topNodeIDs[0][0] + topNodeIDs[1][0]+2
##    curLocation = (pointA[0] + (pointB[0]-pointA[0])*((topNodeIDs[0][0]+1)/totError), pointA[1] + (pointB[1]-pointA[1])*((topNodeIDs[0][0]+1)/totError))
##    closestNode = topNodeIDs[0]
    
    """if curLocation and prevLocation and ((curLocation[0]-prevLocation[0])**2 + (curLocation[1]+prevLocation[1])**2)**0.5 > 0.2 and tries != 1:
        curLocation = prevLocation
        tries += 1
    else:
        tries = 0
    """

    return curLocation

    

#Destination should be a ref point ID
def getPath(dest):
    global pointA, pointB

    if dest in pairToIndex:
        destination = pairToIndex[dest]
        #lineSegList = [(closestNode[0], curLocation)]
        dists = [[99999, []] for i in range(refCount)]
        dists[pointA] = (hypot(curLocation[0]-refPoints[pointA].pos[0],curLocation[1]-refPoints[pointA].pos[1]), [])
        dists[pointB] = (hypot(curLocation[0]-refPoints[pointB].pos[0],curLocation[1]-refPoints[pointB].pos[1]), [])
        points = Queue()
        points.put(pointA)
        points.put(pointB)
        while not points.empty():
            cur = points.get()
            for edge in graph[cur]:
                if dists[edge[0]][0] > dists[cur][0]+edge[1]:
                    dists[edge[0]][0] = dists[cur][0]+edge[1]
                    dists[edge[0]][1] = dists[cur][1]+[(cur, edge[0])]
                    points.put(edge[0])
        #print(12345, dists[destination][1])
        z = 0
        for w in dists[destination][1]:
            if pointA in w:
                z = [pointA, curLocation]
                break
            elif pointB in w:
                z = [pointB, curLocation]
                break
        for e in range(len(dists[destination][1])):
            dists[destination][1][e] = [refPoints[dists[destination][1][e][0]].pos, refPoints[dists[destination][1][e][1]].pos]
        if z != 0:
            dists[destination][1].append([curLocation, refPoints[z[0]].pos])
        else:
            dists[destination][1].append([curLocation, refPoints[destination].pos])
        return dists[destination][1]








