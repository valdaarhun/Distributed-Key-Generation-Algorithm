from twisted.internet import reactor

def startupError():
    print('\033[0;31mUsage: main.py [target port] [host port]\033[0m')
    exit(1)

def serverError(error, port):
    print(f'Port in use: {port} {error}\nCan\'t set up node')

def clientError(error, port):
    print(f'Connection refused: {error} {port}')
