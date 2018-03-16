from .geom import pp_dist
from .geom import Point
from .game_map import Map
from . import constants

class Graph:
    # Bottom-Left is (0,0)
    def __init__(self, map, size=1):
        self.nodes = {Point(i,j) : self.Node(Point(i,j)) 
                      for i in range(0,map.width,size) 
                      for j in range(0,map.height,size)}

        plist = [Point(1,0), Point(-1,0), Point(0,1), Point(0,-1)]

        for k,n in self.nodes.items():
            for p in plist:
                if n.loc+p in self.nodes:
                    n.adj.append(self.nodes[n.loc+p])

    class Node:
        def __init__(self, loc):
            self.loc = loc
            self.adj = []

