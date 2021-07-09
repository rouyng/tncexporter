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
    def __init__(self, tnc_url: str, kiss_mode: bool = False, loop: AbstractEventLoop = None):
        self.parsed_url = urlparse(tnc_url)
        self.tnc_host = self.parsed_url.hostname  # tnc host to connect to
        self.tnc_port = int(self.parsed_url.port)  # tnc port to listen on
        self.packet_queue = asyncio.Queue()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if kiss_mode:
            self.kiss_mode = True
            self.connect_kiss(self.tnc_host, self.tnc_port)
        else:
            self.kiss_mode = False
            self.connect_agw(self.tnc_host, self.tnc_port)
        self.api_version = None  # version returned by host API
        self.loop = loop or asyncio.get_event_loop()

    def connect_agw(self, host: str, port: int, retry_delay: int = 10):
        """Connect to a TNC's AGWPE API"""
        while True:
            try:
                logging.info(f"Attempting to connect to TNC at {host}:{port}")
                self.client_socket.connect((host, port))
            except ConnectionRefusedError:
                logging.error(f"Could not connect to TNC at {host}:{port}, connection refused. "
                              f"Retrying in {retry_delay} seconds")
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

    def connect_kiss(self, host: str, port: int, retry_delay: int = 10):
        """Connect to a TNC's KISS TCP interface"""
        while True:
            try:
                logging.info(f"Attempting to connect to TNC at {host}:{port}")
                self.client_socket.connect((host, port))
            except ConnectionRefusedError:
                logging.error(f"Could not connect to TNC at {host}:{port}, connection refused. "
                              f"Retrying in {retry_delay} seconds")
                sleep(retry_delay)
                continue
            else:
                logging.info(f"Connection established to TNC at {host}:{port}")
                break

    def disconnect(self):
        """Close client socket connection"""
        self.client_socket.close()
        logging.info("Closed connection to TNC")

    async def receive_packets(self):
        """
        Continually receive packets from the AGWPE API and append them to the packet list
        as byte strings.
        """
        # set the socket to non-blocking. If this is not set manually in Python 3.7, sock_recv will
        # block other tasks. It is only set once we begin recieving packets for metric calclations,
        # because the earlier socket operations to create a connection to the TNC can run
        # synchronously. Therefore there is no reason to set nonblocking early
        # and create extra complexity.
        self.client_socket.setblocking(False)
        # loop to listen for packets sent from the TNC and add them to the queue for metrics
        # processing
        while True:
            packet_bytes: bytes = b""
            bytes_recv: int = 0
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
                    if self.kiss_mode:
                        self.connect_kiss(self.tnc_host, self.tnc_port)
                    else:
                        self.connect_agw(self.tnc_host, self.tnc_port)
                    continue
                else:
                    packet_bytes += chunk
                    bytes_recv += len(chunk)
            if self.kiss_mode:
                # sometimes, a KISS interface will pass multiple packets. Split by frame delimiter
                # and add each to the queue
                split_packets = packet_bytes.split(b'\xc0')
                for p in split_packets:
                    if len(p) > 0:
                        await self.packet_queue.put(p)
            else:
                await self.packet_queue.put(packet_bytes)
            logging.debug(f"Received packet, total {self.packet_queue.qsize()} in queue")
