import socket
import errno
import socket
import contextlib
import SocketServer

class Server(SocketServer.TCPServer):

    def __init__(
            self, address='localhost', port=9000, message='Message sent',
            timeout=0.5
        ):
        self.address = address
        self.port = port
        self.message = message
        self.timeout = timeout
        
        SocketServer.TCPServer.__init__(
            self, (self.address, self.port), ServerHandler
        )

class ServerHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        self.request.sendall(self.server.message+'\0')
