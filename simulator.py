import heapq
from collections import defaultdict
import random


class Event:
    def __init__(self, time, func, *args, **kwargs):
        self.time = time
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return self.time < other.time


class Simulator:
    instance = None

    @classmethod
    def getinstance(cls):
        if not Simulator.instance:
            Simulator.instance = Simulator()
        return Simulator.instance

    def __init__(self):
        self.event_queue = []
        self.simclock = 0.0
        random.seed(1001)

    def add_event(self, time, func, *args, **kwargs):
        heapq.heappush(self.event_queue, Event(time, func, *args, **kwargs))

    def run(self):
        while len(self.event_queue) > 0:
            event = heapq.heappop(self.event_queue)
            self.simclock = event.time
            if event.args and event.kwargs:
                event.func(event.args, event.kwargs)
            elif event.args:
                event.func(*event.args)
            elif event.kwargs:
                event.func(**event.kwargs)
            else:
                event.func()


class Channel:
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2
        self.message_queue = []
        self.delay = 200

    def push_message(self, message):
        self.message_queue.append(message)


class Network:
    instance = None

    @classmethod
    def getinstance(cls):
        if not Network.instance:
            Network.instance = Network()
        return Network.instance

    def __init__(self):
        self.nodes = {}
        self.delay = 100.0

    def add_node(self, node):
        self.nodes[node.node_id] = node

    def node_by_id(self, node_id):
        return self.nodes[node_id]

    def send(self, frm, to, message):
        sim = Simulator.getinstance()
        delay = self.delay * random.random()
        sim.add_event(sim.simclock + delay, to.recv, sim.simclock + delay, frm, message)


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        network = Network.getinstance()
        network.add_node(self)

    def send(self, other_node, message):
        network = Network.getinstance()
        if isinstance(other_node, Node):
            to = other_node
        else:
            to = network.node_by_id(other_node)
        network.send(self, to, message)

    def recv(self, time, frm, message):
        print('Time %f %s Received from %s this message %s' % (time, self, frm, message))

    def __hash__(self):
        return self.node_id

    def __str__(self):
        return 'Node-%s' % self.node_id



def print_line(line, *args, **kwargs):
    print(line)
    print(*args)
    print(**kwargs)


def main():
    sim = Simulator.getinstance()
    n1 = Node(101)
    n2 = Node(201)
    n3 = Node(301)

    n1.send(n2, 'Hello1')
    n1.send(n2, 'Hello2')
    n1.send(n2, 'Hello3')

    n2.send(n3, 'Aloha1')
    n2.send(n3, 'Aloha2')
    n2.send(n3, 'Aloha3')

    n3.send(n1, 'Hi1')
    n3.send(n1, 'Hi2')
    n3.send(n1, 'Hi3')

    sim.run()


if __name__ == '__main__':
    main()