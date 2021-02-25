"""
This module contains the functionality for connecting to the TNC's TCP/IP interface, monitoring
packets and extracting specific kinds of data to be instrumented.
"""
from urllib.parse import urlparse


class Listener:
    """Class for creating listener objects that connect to AGWPE TCP/IP API and capture packets"""
    def __init__(self, tnc_url: str):
        self.parsed_url = urlparse(tnc_url)
        self.host = self.parsed_url.netloc  # tnc host to connect to
        self.port = self.parsed_url.port  # tnc port to listen on
        self.packets = []  # queue of packets to be parsed/processed by exporter
        self.connect(self.host, self.port)

    def connect(self, host, port):
        """Connect to a TNC's AGWPE API"""
        pass
