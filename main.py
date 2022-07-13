from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet import reactor
import sys

from errors import startupError, serverError, clientError
from p2p import myProtocol, myFactory, gotProtocol

arguments = sys.argv[1:]
if len(arguments) != 1 and len(arguments) != 2:
    startupError()
else:
    # TODO: Exchange host and target ports indices
    host_port = int(arguments[-1])
    target_port = -1 if len(arguments) == 1 else int(arguments[0])

endpoint = TCP4ServerEndpoint(reactor, host_port, interface='127.0.0.1')
connection_factory = myFactory('127.0.0.1', host_port)
connection = endpoint.listen(connection_factory)
connection.addErrback(serverError, host_port)

try:
    print(f'\033[0;32mUUID: {connection_factory.node_id}\033[0m')
except AttributeError:
    pass

try:
    if target_port != -1:
        point = TCP4ClientEndpoint(reactor, '127.0.0.1', target_port)
        d = connectProtocol(point, myProtocol(connection_factory, 2))
        d.addCallback(gotProtocol)
        d.addErrback(clientError, target_port)
    reactor.run()
except AttributeError:
    pass
