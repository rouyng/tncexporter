"""
This module contains the functionality for connecting to the TNC's TCP/IP interface, monitoring
packets and extracting specific kinds of data to be instrumented.
"""
from urllib.parse import urlparse
import socket

# AGWPE format packet to request version from TNC host
version_request = bytes.fromhex(
    "000000005200000000000000000000000000000000000000000000000000000000000000")

# AGWPE format packet to request monitoring packets be send from host
monitor_request = bytes.fromhex(
    "000000006D00000000000000000000000000000000000000000000000000000000000000")


class Listener:
    """Class for creating listener objects that connect to AGWPE TCP/IP API and capture packets"""
    def __init__(self, tnc_url: str):
        self.parsed_url = urlparse(tnc_url)
        self.tnc_host = self.parsed_url.netloc  # tnc host to connect to
        self.tnc_port = self.parsed_url.port  # tnc port to listen on
        self.packets = []  # queue of packets to be parsed/processed by exporter
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(self.tnc_host, self.tnc_port)
        self.api_version = None  # version returned by host API

    def connect(self, host, port):
        """Connect to a TNC's AGWPE API"""
        self.client_socket.connect((host, port))
        # TODO: send "R" packet, receive version number
        # TODO: send "g" packet, receive port capabilities
        self.client_socket.sendall(monitor_request)  # ask tnc to send monitor packets

    def receive(self):
        chunks = []
        bytes_recv = 0
        # TODO: modify chunk receiving algorithim to detect packet lenght, which is
        # 4 bytes encoding an unsigned integer at positions 29-33
        while bytes_recv < 36:
            chunk = self.client_socket.recv(36)
            if chunk == b'':
                raise Exception("Socket connection broken")
            chunks.append(chunk)
            bytes_recv += len(chunk)
        packet = chunks
        self.packets.append(packet)
