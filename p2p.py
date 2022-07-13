from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from uuid import uuid4
from pprint import pprint
import json

from errors import serverError, clientError
import computation
import message
import test

id_gen = lambda: str(uuid4())

class myProtocol(Protocol):
    def __init__(self, factory, peer_type):
        self.factory = factory
        self.node_id = self.factory.node_id
        self.remote_node_id = None
        self.peer_type = peer_type

    def connectionMade(self):
        host = self.transport.getHost()
        remote = self.transport.getPeer()
        self.remote_ip = remote.host + ':' + str(remote.port)
        self.host_ip = host.host + ':' + str(host.port)
        # self.factory.protocols[self.remote_ip] = self
        # pprint(self.factory.protocols)

    def connectionLost(self, reason):
        if self.remote_node_id in self.factory.peers:
            self.factory.peers.pop(self.remote_node_id)
            self.factory.protocols.pop(self.remote_node_id)
            try:
                self.factory.shares.pop(self.remote_node_id)
            except:
                pass
        print(f'\033[1;32m{self.remote_node_id} disconnected\033[0m')

    def send_peers(self):
        msg = message.msg_peers(self.node_id, self.factory.peers)
        send_msg(self, msg)

    def add_peer(self, data):
        self.factory.peers[self.remote_node_id] = data['msg']
        print('List of peers')
        pprint(self.factory.peers)
    
    def broadcast(self):
        if self.factory.broadcast is False:
            self.factory.private_shares = computation.generate_shares(self.factory.secret, len(self.factory.peers), self.factory.mod)
            test.test(self.factory.private_shares, self.factory.secret, self.factory.mod)
            values = self.factory.private_shares
            peers = self.factory.peers
            idx = 0
            for peer in peers:
                addr = peers[peer].split(':')
                ip, port = addr[0], int(addr[1])
                if peer != self.node_id:
                    msg = message.msg_share(self.node_id, values[idx])
                    send_msg(self.factory.protocols[peer][1], msg)
                else:
                    self.factory.recv_shares[self.node_id] = values[idx]
                idx += 1
        self.factory.broadcast = True

    def dataReceived(self, recv):
        for data in recv.splitlines():
            data = data.strip().decode()
            data = json.loads(data)
            if data['msg_type'] == 'hello':
                self.handle_hello(data)
            elif data['msg_type'] == 'ack_hello':
                self.handle_ack_hello(data)
            elif data['msg_type'] == 'peers':
                self.handle_peers(data)
            elif data['msg_type'] == 'get_peers':
                self.handle_get_peers()
            elif data['msg_type'] == 'init':
                self.handle_init(data['msg'])
            elif data['msg_type'] == 'broadcast':
                self.broadcast()
            elif data['msg_type'] == 'get_share':
                self.handle_get_share()
            elif data['msg_type'] == 'share':
                self.handle_share(data)
                # if (len(self.factory.recv_shares) == len(self.factory.peers)):
                #     ip, port = self.factory.control_address.split(':')[0], int(self.factory.control_address.split(':')[1])
                #     point = TCP4ClientEndpoint(reactor, ip, port)
                #     client_conn = connectProtocol(point, myProtocol(self.factory, 2))
                #     client_conn.addCallback(gotControl)
                #     client_conn.addErrback(clientError, port)
            elif data['msg_type'] == 'priv_key_share':
                self.handle_priv_key_share(data['msg'])
            elif data['msg_type'] == 'pub_key_share':
                self.handle_pub_key_share(data['msg'])
            elif data['msg_type'] == 'info':
                self.handle_set_info(data['msg'])
    
    def sum_private_shares(self):
        y_points = [i[1] for i in self.factory.recv_shares]
        share_sum = sum(y_points)
        return (self.factory.recv_shares[0][0], share_sum)
    
    def handle_get_share(self):
        share = self.sum_private_shares()
        payload = json.dumps({
            "private_share": share,
            "pub_key": (self.factory.pub_key.x, self.factory.pub_key.y)
        })
        msg = message.msg_send_share(self.node_id, payload)
        send_msg(self, msg)

    def handle_set_info(self, data):
        payload = json.loads(data)
        self.factory.n = payload['n']
        self.factory.t = payload['t']
        payload = json.loads(payload['x_points'])
        x_points = list(map(int, list(payload.keys())))
        uuids = list(payload.values())
        self.factory.x_points = dict(zip(x_points, uuids))
        # print(self.factory.x_points)
    
    def handle_pub_key_share(self, data):
        if self.factory.broadcast == False:
            self.factory.public_key_share = computation.ECC(self.factory.private_share)
            self.factory.public_key_shares = [self.factory.public_key_share]
            # print(self.factory.public_key_share)
            payload = (self.factory.public_key_share.x, self.factory.public_key_share.y)
            msg = message.msg_send_pub_k(self.node_id, payload)
            for i in self.factory.protocols:
                send_msg(self.factory.protocols[i][1], msg)
        self.factory.broadcast = True
        self.factory.public_key_shares.append(computation.coords_to_point(data[0], data[1]))
        if len(self.factory.public_key_shares) == len(self.factory.peers):
            self.factory.pub_key = self.factory.public_key_shares[0]
            for i in range(1, len(self.factory.public_key_shares), 1):
                self.factory.pub_key += self.factory.public_key_shares[i]
            # print(self.factory.pub_key)

    def handle_priv_key_share(self, secret):
        self.factory.priv_key_share = secret[0]
        self.factory.public_key = secret[1]
        print(self.factory.priv_key_share, self.factory.public_key, sep=' ')

    # def send_ack_control(self):
    #     sum_shares = sum(self.factory.recv_shares.values())
    #     msg = message.msg_ack_control(self.node_id, sum_shares)
    #     send_msg(self, msg)

    def handle_init(self, data):
        self.factory.n = data[0]
        self.factory.t = data[1]

        secret_sharing = computation.Shamir_Secret_Sharing(self.factory.n, self.factory.t)
        self.factory.private_share = computation.rand_num()
        print(f'Sec: {self.factory.private_share}')
        self.factory.priv_key_shares = secret_sharing.gen_shares(self.factory.private_share)
        print(f'Sec (testing SSS...): {secret_sharing.regenerate(self.factory.priv_key_shares)}')
        print(f'Shares: {self.factory.priv_key_shares}')
        self.factory.x_points = dict(zip([p[0] for p in self.factory.priv_key_shares], list(self.factory.peers.keys())))
        payload = json.dumps({
            "n": self.factory.n,
            "t": self.factory.t,
            "x_points": json.dumps(self.factory.x_points)
        })
        # print(self.factory.x_points)
        msg = message.msg_send_info(self.node_id, payload)
        for i in self.factory.protocols:
            send_msg(self.factory.protocols[i][1], msg)

        for i in self.factory.priv_key_shares:
            x_point = i[0]
            share = i[1]
            uuid = self.factory.x_points[x_point]
            if uuid in self.factory.protocols:
                peer = self.factory.protocols[uuid][1]
                msg = message.msg_share(self.node_id, i)
                send_msg(peer, msg)
            else:
                self.factory.recv_shares.append((x_point, share))
        self.factory.share = True

        self.factory.public_key_share = computation.ECC(self.factory.private_share)
        self.factory.public_key_shares = [self.factory.public_key_share]
        payload = (self.factory.public_key_share.x, self.factory.public_key_share.y)
        msg = message.msg_send_pub_k(self.node_id, payload)
        for i in self.factory.protocols:
            send_msg(self.factory.protocols[i][1], msg)
        self.factory.broadcast = True
    
    def handle_share(self, data):
        # print(f"MSG: {data['msg']}")
        self.factory.recv_shares.append(tuple(data['msg']))
        # print(self.factory.recv_shares)
        if self.factory.share == False:
            secret_sharing = computation.Shamir_Secret_Sharing(self.factory.n, self.factory.t)
            self.factory.private_share = computation.rand_num()
            print(f'Sec: {self.factory.private_share}')
            self.factory.priv_key_shares = secret_sharing.gen_shares(self.factory.private_share)
            print(f'Sec (testing SSS...): {secret_sharing.regenerate(self.factory.priv_key_shares)}')
            x_points = list(self.factory.x_points.keys())
            self.factory.priv_key_shares = secret_sharing.gen_shares_with_x_points(self.factory.private_share, x_points)
            print(f'Shares: {self.factory.priv_key_shares}')
            for i in self.factory.priv_key_shares:
                x_point = i[0]
                share = i[1]
                uuid = self.factory.x_points[x_point]
                if uuid in self.factory.protocols:
                    peer = self.factory.protocols[uuid][1]
                    # print(i)
                    msg = message.msg_share(self.node_id, i)
                    # print(msg)
                    send_msg(peer, msg)
                else:
                    self.factory.recv_shares.append((x_point, share))
        self.factory.share = True
        # print(self.factory.recv_shares)
        if len(self.factory.recv_shares) == len(self.factory.peers):
            pprint(self.factory.recv_shares)

    def handle_get_peers(self):
        # Do I need self.node_id here?
        msg = message.msg_send_peers(self.node_id, self.factory.peers)
        send_msg(self, msg)

    def handle_hello(self, data):
        self.remote_node_id = data['uuid']
        if self.remote_node_id == self.node_id:
            print('\033[1;31mConnected to self\033[0m')
            self.transport.loseConnection()
        else:
            self.factory.protocols[self.remote_node_id] = (self.remote_ip, self)
            # pprint(self.factory.protocols)
            msg = message.msg_ack_hello(self.node_id, self.factory.addr)
            send_msg(self, msg)

    def send_hello(self):
        msg = message.msg_hello(self.node_id)
        send_msg(self, msg)
        
    def handle_ack_hello(self, data):
        print(f'\033[1;32mConnected to {self.remote_ip} (UUID: {self.node_id}) successfully\033[0m')
        self.remote_node_id = data['uuid']
        self.add_peer(data)
        self.send_peers()

    def handle_peers(self, data):
        potential_peers = data['msg']
        for peer in potential_peers:
            addr = potential_peers[peer].split(':')
            ip, port = addr[0], int(addr[1])
            if peer != self.node_id and peer not in self.factory.peers:
                point = TCP4ClientEndpoint(reactor, ip, port)
                client_conn = connectProtocol(point, myProtocol(self.factory, 2))
                client_conn.addCallback(gotProtocol)
                client_conn.addErrback(clientError, port)


class myFactory(Factory):
    def __init__(self, ip, port):
        self.addr = ip + ':' + str(port)
        self.mod = 10007
        self.broadcast = False
        self.share = False

    def startFactory(self):
        self.node_id = id_gen()
        self.secret = computation.rand_num() % self.mod
        self.peers = {self.node_id: self.addr}
        self.protocols = {}
        self.recv_shares = []

    def buildProtocol(self, addr):
        return myProtocol(self, 1)

def gotProtocol(p):
    print('\033[1;33mConnecting...\033[0m')
    p.send_hello()

# def gotControl(p):
#     p.send_ack_control()

def send_msg(connection_protocol, msg):
    connection_protocol.transport.write(msg + b'\n')
