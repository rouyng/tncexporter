"""
This module contains the functionality for connecting to the TNC's TCP/IP interface, monitoring
packets and extracting specific kinds of data to be instrumented.
"""
import asyncio
from urllib.parse import urlparse
import socket
import logging
from asyncio.events import AbstractEventLoop

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
    def __init__(self, tnc_url: str,  loop: AbstractEventLoop = None):
        self.parsed_url = urlparse(tnc_url)
        self.tnc_host = self.parsed_url.hostname  # tnc host to connect to
        self.tnc_port = int(self.parsed_url.port)  # tnc port to listen on
        self.packets = []  # queue of raw packet bytestrings to be parsed/processed by exporter
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(self.tnc_host, self.tnc_port)
        self.api_version = None  # version returned by host API
        self.loop = loop or asyncio.get_event_loop()

    def connect(self, host, port):
        """Connect to a TNC's AGWPE API"""
        try:
            self.client_socket.connect((host, port))
        except ConnectionRefusedError:
            logging.error(f"Could not connect to TNC at {host}:{port}, connection refused")
            raise ConnectionRefusedError
        else:
            logging.info(f"Connection established to TNC at {host}:{port}")
            # TODO: send "R" packet, receive version number
            # TODO: send "g" packet, receive port capabilities
            self.client_socket.sendall(MONITOR_REQUEST)  # ask tnc to send monitor packets

    def disconnect(self):
        """Close client socket connection"""
        self.client_socket.close()
        logging.info("Closed connection to TNC")

    async def receive_packets(self):
        """Receive a packet from the AGWPE API and append it to the packet list as a byte string"""
        while True:
            # TODO: handle ConnectionResetError
            chunks = b""
            bytes_recv = 0
            while bytes_recv < 36:
                chunk = await self.loop.sock_recv(self.client_socket, 4096)
                if chunk == b'':
                    raise Exception("Socket connection broken")
                chunks += chunk
                bytes_recv += len(chunk)
            self.packets.append(chunks)
            logging.info(f"Received packet, total {len(self.packets)}")

    def read_packet_queue(self):
        """Returns packets in queue for exporter processing and clears queue"""
        packet_batch = self.packets.copy()
        self.packets = []
        logging.info(f"{len(packet_batch)} packets read from queue")
        return packet_batch
