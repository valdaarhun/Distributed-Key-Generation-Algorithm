from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
# from tinyec.ec import SubGroup, Curve
from pprint import pprint
from random import sample
import json
import sys

from errors import startupError, serverError, clientError
from computation import Shamir_Secret_Sharing, ECC
import message

class myProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.remote_node_id = None

    def connectionMade(self):
        host = self.transport.getHost()
        remote = self.transport.getPeer()
        self.remote_ip = remote.host + ':' + str(remote.port)
        self.host_ip = host.host + ':' + str(host.port)
  
    def dataReceived(self, recv):
        for data in recv.splitlines():
            data = data.strip().decode()
            data = json.loads(data)
            if data['msg_type'] == 'send_peers':
                print('Available peers are:')
                pprint(data['msg'])
                self.factory.peers = data['msg']
                self.init(len(data['msg']))
                # self.broadcast()
            elif data['msg_type'] == 'init_control':
                payload = (self.factory.peers, self.factory.t)
                msg = message.msg_send_peers('control', payload)
                send_msg(self, msg)
            elif data['msg_type'] == 'init_ack':
                # self.broadcast()
                print('Done')
            # elif data['msg_type'] == 'ack_control':
            #     self.factory.recv_shares.append(data['msg'])
            #     print(data['uuid'], data['msg'], sep=' ')
            #     self.factory.protocols[data['uuid']] = self
            #     # pprint(self.factory.protocols)
            #     if (len(self.factory.recv_shares) == self.factory.n):
            #         self.generate_keys(self.factory.recv_shares)
            #         idx = 0
            #         pprint(self.factory.priv_key_shares)
            #         for peer in self.factory.protocols:
            #             msg = message.priv_key_share((self.factory.priv_key_shares[idx], self.factory.public_key))
            #             idx += 1
            #             send_msg(self.factory.protocols[peer], msg)
    
    # def generate_keys(self, secrets):
    #     private_key = sum(secrets) % self.factory.mod
    #     secret_sharing = Shamir_Secret_Sharing(self.factory.n, self.factory.t)
    #     self.factory.priv_key_shares = secret_sharing.gen_shares(private_key)
    #     self.factory.public_key = ECC(private_key)
    #     print('\033[33mShamir\'s shares:\033[0m')
    #     pprint(self.factory.priv_key_shares)
    #     print(f'\033[1;33mPrivate key after additive sharing:\033[0m {hex(private_key)[2:]}')
    #     print(f'\033[1;32mPublic key after applying ECC:\033[0m {self.factory.public_key}')
        # gen_from_shares = sample(self.factory.priv_key_shares, self.factory.t)
        # print(gen_from_shares)
        # regenerated_secret = secret_sharing.regenerate(gen_from_shares)
        # print(f'gen priv: {regenerated_secret}')

    def get_peers(self):
        msg = message.msg_get_peers()
        send_msg(self, msg)
    
    def init(self, n):
        self.factory.n = n
        self.factory.t = (3 * n) // 4
        # payload = self.factory.host_ip
        payload = (self.factory.n, self.factory.t)
        msg = message.msg_init('control', payload)
        send_msg(self, msg)
    
    def broadcast(self):
        msg = message.msg_broadcast()
        send_msg(self, msg)
     
class myFactory(Factory):
    def startFactory(self):
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

def send_msg(connection_protocol, msg):
    connection_protocol.transport.write(msg + b'\n')

arguments = sys.argv[1:]
if len(arguments) != 1:
    startupError()
else:
    target_port = int(arguments[-1])
    host_port = 31336

endpoint = TCP4ServerEndpoint(reactor, host_port, interface='127.0.0.1')
connection_factory = myFactory()
connection = endpoint.listen(connection_factory)
connection.addErrback(serverError, host_port)

try:
    point = TCP4ClientEndpoint(reactor, '127.0.0.1', target_port)
    d = connectProtocol(point, myProtocol(connection_factory))
    d.addCallback(gotProtocol)
    d.addErrback(clientError, target_port)
    reactor.run()
except AttributeError:
    pass
