import heapq
from collections import defaultdict
from enum import Enum
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
            if event.func:
                if event.args and event.kwargs:
                    event.func(*event.args, **event.kwargs)
                elif event.args:
                    event.func(*event.args)
                elif event.kwargs:
                    event.func(**event.kwargs)
                else:
                    event.func()


class Channel:
    def __init__(self, network, node1, node2):
        self.network = network
        self.node1 = node1
        self.node2 = node2
        self.message_queue = []
        self.delay = 200e-3

    def push_message(self, message):
        sim = Simulator.getinstance()
        self.message_queue.append(message)
        if len(self.message_queue) == 1:   # first message, schedule pop
            delay = self.delay * random.random()
            sim.add_event(sim.simclock + delay, self.pop_message)

    def pop_message(self):
        sim = Simulator.getinstance()
        if len(self.message_queue) > 0:
            message = self.message_queue.pop(0)
            self.network.sendnow(self.node1, self.node2, message)

            # Schedule the next pop from the same channel
            if len(self.message_queue) > 0:
                delay = self.delay * random.random()
                sim.add_event(sim.simclock + delay, self.pop_message)


class ChannelType(Enum):
    FIFO = 1
    RANDOM = 2


class Network:
    instance = None
    channel_type = ChannelType.RANDOM

    @classmethod
    def getinstance(cls):
        if not Network.instance:
            Network.instance = Network()
        return Network.instance

    @classmethod
    def set_channel_type(cls, type):
        Network.channel_type = type

    def __init__(self):
        self.nodes = {}
        self.channels = {}
        self.delay = 200e-3

    def add_node(self, node):
        if node in self.nodes:
            return

        self.nodes[node] = node
        if Network.channel_type == ChannelType.FIFO:
            for n1 in self.nodes.values():
                if n1 != node:
                    if n1 not in self.channels:
                        self.channels[n1] = {}
                    self.channels[n1][node] = Channel(self, n1, node)
                    self.channels[node] = {}
                    for n1 in self.nodes.values():
                        if n1 != node:
                            self.channels[node][n1] = Channel(self, node, n1)

    def node_by_id(self, node_id):
        return self.nodes[node_id]

    def sendnow(self, frm, to, message):
        sim = Simulator.getinstance()
        if to.is_alive:
            to.recv(sim.simclock, frm, message)

    def send(self, frm, to, message):
        sim = Simulator.getinstance()
        if Network.channel_type == ChannelType.RANDOM:
            delay = self.delay * random.random()
            sim.add_event(sim.simclock + delay, self.sendnow, frm, to, message)
        elif Network.channel_type == ChannelType.FIFO:
            channel = self.channels[frm][to]
            channel.push_message(message)


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.is_alive = True
        network = Network.getinstance()
        network.add_node(self)

    def failed(self):
        self.is_alive = False

    def recovered(self):
        self.is_alive = False

    def send(self, other_node, message):
        network = Network.getinstance()
        if isinstance(other_node, Node):
            to = other_node
        else:
            to = network.node_by_id(other_node)
        network.send(self, to, message)

    def send_after(self, delay, other_node, message):
        sim = Simulator.getinstance()
        if delay >= 0:
            sim.add_event(sim.simclock + delay, self.send, other_node, message)
        else:
            raise Exception('Invalid delay value, should be non-negative')

    def recv(self, time, frm, message):
        if not self.is_alive:
            return
        print('Time %f %s Received from %s this message %s' % (time, self, frm, message))

    @staticmethod
    def add_callback(delay, func, *args, **kwargs):
        sim = Simulator.getinstance()
        if delay >= 0:
            sim.add_event(sim.simclock + delay, func, *args, **kwargs)
        else:
            raise Exception('Invalid delay value, should be non-negative')

    def __hash__(self):
        return self.node_id

    def __str__(self):
        return 'Node-%s' % self.node_id

    def __eq__(self, other):
        return self.node_id == other.node_id

    def __lt__(self, other):
        return self.node_id < other.node_id


def driver():
    sim = Simulator.getinstance()
    Network.set_channel_type(ChannelType.RANDOM)

    n1 = Node(101)
    n2 = Node(201)
    n3 = Node(301)
    n4 = Node(401)
    #n4.failed()
    #n4.add_callback(0.01, n4.recovered)

    n1.send(n2, 'Hello1')
    n1.send(n2, 'Hello2')
    n1.send(n2, 'Hello3')

    n1.send(n4, 'Hello1')
    n1.send(n4, 'Hello2')
    n1.send(n4, 'Hello3')

    n3.send(n2, 'Aloha1')
    n3.send(n2, 'Aloha2')
    n3.send(n2, 'Aloha3')

    n3.send(n4, 'Aloha1')
    n3.send(n4, 'Aloha2')
    n3.send(n4, 'Aloha3')

    sim.run()


if __name__ == '__main__':
    driver()