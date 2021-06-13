"""
This module contains the functionality for connecting to the TNC's TCP/IP interface, monitoring
packets and extracting specific kinds of data to be instrumented.
"""
import asyncio
from urllib.parse import urlparse
import socket
import logging
from asyncio.events import AbstractEventLoop
from time import sleep
import sys

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

    def connect(self, host: str, port: int, retry_delay: int = 10):
        """Connect to a TNC's AGWPE API"""
        while True:
            try:
                logging.info(f"Attempting to connect to TNC at {host}:{port}")
                self.client_socket.connect((host, port))
            except ConnectionRefusedError:
                logging.error(f"Could not connect to TNC at {host}:{port}, connection refused")
                logging.error(f"Retrying in {retry_delay} seconds")
                sleep(retry_delay)
                continue
            else:
                logging.info(f"Connection established to TNC at {host}:{port}")
                break
        # send version request packet to TNC
        # this provides a check as to whether you are connecting to an actual TNC that
        # exposes an AGWPE API, as well as logging the version response for debugging
        logging.debug("Sending version request to TNC")
        self.client_socket.sendall(VERSION_REQUEST)
        version_packet = b""
        bytes_recv = 0
        while bytes_recv < 36:
            chunk = self.client_socket.recv(4096)
            if chunk == b'':
                raise ConnectionResetError("Socket connection broken")
            version_packet += chunk
            bytes_recv += len(chunk)
        if chr(version_packet[4]) == 'R':
            # read major and minor versions from packet sent by TNC
            maj_ver = int.from_bytes(version_packet[36:38], 'little')
            min_ver = int.from_bytes(version_packet[40:42], 'little')
            logging.debug(f"Received TNC version info: {maj_ver}.{min_ver} ")
            self.client_socket.sendall(MONITOR_REQUEST)  # ask tnc to send monitor packets
        else:
            # If the version response packet doesn't report the expected R packet type in byte 4,
            # shut everything down as you're probably not communicating with the AGWPE API
            logging.error("Did not receive expected reply when connecting to TNC. Quitting.")
            logging.debug("Received the following packet in response to version request:",
                          version_packet)
            sys.exit()
        # TODO: send "g" packet, receive port capabilities

    def disconnect(self):
        """Close client socket connection"""
        self.client_socket.close()
        logging.info("Closed connection to TNC")

    async def receive_packets(self):
        """
        Continually receive packets from the AGWPE API and append them to the packet list
        as byte strings.
        """
        while True:
            chunks = b""
            bytes_recv = 0
            while bytes_recv < 36:
                try:
                    chunk = await self.loop.sock_recv(self.client_socket, 4096)
                    if chunk == b'':
                        raise ConnectionResetError("Socket connection broken")
                except ConnectionResetError:
                    logging.error("Connection to TNC was reset")
                    self.client_socket.close()
                    # remake client socket
                    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.connect(self.tnc_host, self.tnc_port)
                    continue
                else:
                    chunks += chunk
                    bytes_recv += len(chunk)
            self.packets.append(chunks)
            logging.debug(f"Received packet, total {len(self.packets)} in queue")

    def read_packet_queue(self):
        """Returns packets in queue for exporter processing and clears queue"""
        packet_batch = self.packets.copy()
        self.packets = []
        logging.debug(f"{len(packet_batch)} packets read from queue")
        return packet_batch
