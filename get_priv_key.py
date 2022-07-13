from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
# from tinyec.ec import SubGroup, Curve
from pprint import pprint
from random import sample
import json
import sys

from errors import startupError, serverError, clientError
from computation import Shamir_Secret_Sharing, compress_public_key
import message
# from p2p import myProtocol, myFactory, gotProtocol

class myProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
  
    def dataReceived(self, recv):
        for data in recv.splitlines():
            data = data.strip().decode()
            data = json.loads(data)
            if data['msg_type'] == 'send_peers':
                self.factory.peers = data['msg'][0]
                self.factory.t = data['msg'][1]
                # pprint(self.factory.peers)
                self.select_t_nodes()
            elif data['msg_type'] == 'send_share':
                payload = json.loads(data['msg'])
                # pprint(payload)
                self.factory.public_key = payload['pub_key']
                self.factory.recv_shares.append(payload['private_share'])
                if len(self.factory.recv_shares) == self.factory.t:
                    self.factory.public_key = compress_public_key(self.factory.public_key[0], self.factory.public_key[1])
                    print(f'\033[1;32mPublic key generated:\033[0m {self.factory.public_key}')
                    pprint(self.factory.recv_shares)
                    self.generate_private_key()

    def get_share(self):
        msg = message.msg_get_share()
        send_msg(self, msg)
    
    def print_sampled_nodes(self, addresses):
        sampled_nodes = []
        for peer in self.factory.peers:
            if self.factory.peers[peer] in addresses:
                sampled_nodes.append(peer)
        print('t nodes chosen for key regeneration')
        pprint(sampled_nodes)
    
    def select_t_nodes(self):
        addresses = list(self.factory.peers.values())
        addresses = sample(addresses, self.factory.t)
        self.print_sampled_nodes(addresses)
        for addr in addresses:
            ip, port = addr.split(':')[0], int(addr.split(':')[1])
            point = TCP4ClientEndpoint(reactor, '127.0.0.1', port)
            d = connectProtocol(point, myProtocol(connection_factory))
            d.addCallback(gotNode)
            d.addErrback(clientError, target_port)
    
    def generate_private_key(self):
        secret_sharing = Shamir_Secret_Sharing(len(self.factory.peers), self.factory.t)
        regenerated_secret = secret_sharing.regenerate(self.factory.recv_shares)
        print(f'\033[1;32mPrivate key generated using Lagrange Interpolation:\033[0m {regenerated_secret}')

    def get_peers(self):
        msg = message.msg_init_control()
        send_msg(self, msg)
     
class myFactory(Factory):
    def __init__(self):
        self.peers = {}
        self.recv_shares = []
        self.protocols = {}
        self.mod = 10007
        self.host_ip = '127.0.0.1:31336'

    def buildProtocol(self, addr):
        return myProtocol(self)

def gotProtocol(p):
    print('\033[1;33mConnecting...\033[0m')
    p.get_peers()

def gotNode(p):
    p.get_share()

def send_msg(connection_protocol, msg):
    connection_protocol.transport.write(msg + b'\n')

host_port = 31335
target_port = 31336

connection_factory = myFactory()

try:
    point = TCP4ClientEndpoint(reactor, '127.0.0.1', target_port)
    d = connectProtocol(point, myProtocol(connection_factory))
    d.addCallback(gotProtocol)
    d.addErrback(clientError, target_port)
    reactor.run()
except AttributeError:
    pass
