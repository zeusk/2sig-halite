import unittest
from ..game_map import Map
from ..pathfinding import Graph
import time

class Test_Pathfinding(unittest.TestCase):
    def setUp(self):
        width = 100
        height = 100
        self.map = Map(None, width,height)

    def test_init(self):
        start_time = time.process_time()
        graph = Graph(self.map)
        end_time = time.process_time()
        print(str(end_time - start_time))
        self.assertTrue(len(graph.nodes) == self.map.width*self.map.height)

if __name__ == '__main__':
    unittest.main()