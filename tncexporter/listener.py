"""
This module contains the functionality for connecting to the TNC's TCP/IP interface, monitoring
packets and extracting specific kinds of data to be instrumented.
"""
from urllib.parse import urlparse
import socket

# AGWPE format packet to request version from TNC host
VERSION_REQUEST = b"\x00\x00\x00\x00\x52\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                  b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                  b"\x00\x00\x00\x00"

# AGWPE format packet to request monitoring packets be send from host
MONITOR_REQUEST = b"\x00\x00\x00\x00\x6D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                  b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                  b"\x00\x00\x00\x00"


class Listener:
    """Class for creating listener objects that connect to AGWPE TCP/IP API and capture packets"""
    def __init__(self, tnc_url: str):
        self.parsed_url = urlparse(tnc_url)
        self.tnc_host = self.parsed_url.hostname  # tnc host to connect to
        self.tnc_port = int(self.parsed_url.port)  # tnc port to listen on
        self.packets = []  # queue of raw packet bytestrings to be parsed/processed by exporter
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(self.tnc_host, self.tnc_port)
        self.api_version = None  # version returned by host API

    def connect(self, host, port):
        """Connect to a TNC's AGWPE API"""
        self.client_socket.connect((host, port))
        # TODO: send "R" packet, receive version number
        # TODO: send "g" packet, receive port capabilities
        self.client_socket.sendall(MONITOR_REQUEST)  # ask tnc to send monitor packets

    def receive_packet(self):
        """Receive a packet from the AGWPE API and append it to the packet list as a byte string"""
        chunks = b""
        bytes_recv = 0
        while bytes_recv < 36:
            chunk = self.client_socket.recv(4096)
            if chunk == b'':
                raise Exception("Socket connection broken")
            chunks += chunk
            bytes_recv += len(chunk)
        self.packets.append(chunks)

    def start(self):
        """This function runs after a connection is established and continuously receives
        packets until interrupted"""
        # TODO: make this placeholder function asynchronous
        while True:
            self.receive_packet()
