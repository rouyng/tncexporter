"""
Parser functions to extract relevant data from AGW or KISS format packets
"""
import datetime
import logging
import re
from math import asin, cos, sin, sqrt, radians
from typing import Tuple

class PacketInfo:
    """Object for parsing and storing AX.25 packet metadata"""

    def __init__(self, packet_bytes: bytes, kiss: bool = False):
        self.raw_bytes: bytes = packet_bytes
        logging.debug(f"Parsing packet bytes: {repr(self.raw_bytes)}")
        self.frame_type: str = "Unknown"  # type of frame (U, I, S, T, other)
        self.data_len: int = 0  # length of data in packet (inclusive of 36 byte header)
        self.data_type: str = "Unknown"  # Describes format of data in the information field
        self.info_field: bytes = b""  # Contents of information field
        self.call_from: str = ""  # originating callsign
        self.call_to: str = ""  # destination callsign
        # timestamp of when packet was received by TNC
        self.timestamp: datetime.time = datetime.time(hour=0,
                                                      minute=0,
                                                      second=0)
        # tuple containing two floats representing latitude and longitude
        self.lat_lon: tuple = (None, None)
        self.hops_count: int = 0  # number of hops. Non-digipeated packets should have 0
        self.hops_path: list[str] = []  # list of hop callsigns
        if kiss:
            self._parse_packet_kiss(packet_bytes)
        else:
            self._parse_packet_agw(packet_bytes)

    def _parse_coordinates(self, data_field: str):
        """
        Parses latitude and longitude coordinates stored as plaintext in the information field of an
        APRS packet. Does not parse compressed format or Mic-E format position reports
        :param data_field: Data/information field of APRS packet
        """
        latitude = None
        longitude = None
        try:
            # parse latitude and longitude from position packets
            latlon_regex = r"([0-9][0-9][0-9][0-9]\.[0-9][0-9])(?:[0-9]|,){0,5}(N|S).{0,2}" \
                           r"([0-1][0-9][0-9][0-9][0-9]\.[0-9][0-9])(?:[0-9]|,){0,5}(E|W)"
            latlon_match = re.search(latlon_regex, data_field)
            if latlon_match is not None:
                logging.debug(f"latlon regex results: {latlon_match.groups()}")
                raw_lat = latlon_match[1]
                lat_direction = latlon_match[2]
                raw_lon = latlon_match[3]
                lon_direction = latlon_match[4]
                if lat_direction == 'N':
                    latitude = round(float(raw_lat) / 100, 4)
                elif lat_direction == 'S':
                    latitude = round(-float(raw_lat) / 100, 4)
                else:
                    latitude = None
                if lon_direction == 'E':
                    longitude = round(float(raw_lon) / 100, 4)
                elif lon_direction == 'W':
                    longitude = round(-float(raw_lon) / 100, 4)
                else:
                    longitude = None
            # TODO: decode position reports from Mic-E and APRS compressed formats
        except (IndexError, ValueError):
            pass
        self.lat_lon = (latitude, longitude)

    def haversine_distance(
            self,
            tnc_pos: Tuple[float, float],
            radius: float = 6371.0e3
    ) -> float:
        """
        Calculate the distance between two points on a sphere (e.g. Earth).
        If no radius is provided then the default Earth radius, in meters, is
        used.
        The haversine formula provides great-circle distances between two points
        on a sphere from their latitudes and longitudes using the law of
        haversines, relating the sides and angles of spherical triangles.
        Based on the haversine_distance function used here:
        https://github.com/claws/dump1090-exporter/blob/master/src/dump1090exporter/exporter.py
        `Reference <https://en.wikipedia.org/wiki/Haversine_formula>`_
        :param tnc_pos: a tuple defining (lat, lon) in decimal degrees
        :param radius: radius of sphere in meters.
        :returns: distance between two points in meters.
        :rtype: float
        """
        lat1, lon1, lat2, lon2 = [radians(x) for x in (*self.lat_lon, *tnc_pos)]

        hav = (
                sin((lat2 - lat1) / 2.0) ** 2
                + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2.0) ** 2
        )
        distance = 2 * radius * asin(sqrt(hav))
        logging.debug(f"Calculated distance between {self.lat_lon} and {tnc_pos} = {distance:.4f}")
        return distance

    def _parse_packet_agw(self, raw_packet: bytes):
        """Parse AGW-format packet bytes, create a PacketInfo object
        :param raw_packet: packet bytes
        """
        try:
            self.frame_type = chr(raw_packet[4]).upper()
            self.call_from = raw_packet[8:18].strip(b'\x00').decode("ascii", errors="replace")
            self.call_to = raw_packet[18:28].strip(b'\x00').decode("ascii", errors="replace")
            data_bytes = raw_packet[36:].strip(b'\x00')
            self.info_field = data_bytes.split(b'\r')[1]
            self.len_data = len(data_bytes)
            data_string = data_bytes.decode("ascii", errors="replace")
            logging.debug(f"Parsing data field: {repr(data_string)}")
            # parse timestamp
            time_match = re.search("[0-2][0-9]:[0-5][0-9]:[0-5][0-9]", data_string)
            if time_match is not None:
                try:
                    raw_hour = time_match.group()[0:2]
                    raw_min = time_match.group()[3:5]
                    raw_sec = time_match.group()[6:8]
                    self.timestamp = datetime.time(hour=int(raw_hour),
                                                   minute=int(raw_min),
                                                   second=int(raw_sec))
                except TypeError:
                    pass
            try:
                # Parse list of hops
                # This won't parse the hops list in headers that UI-View creates, and possibly
                # some other non-standard header formats as well.
                hops_string = re.findall("Via (.*?) <", data_string)[0]
                # tuple of non-WIDE path types that don't represent hops through a digipeater
                path_types = ('RELAY',
                              'ECHO',
                              'TRACE',
                              'GATE',
                              'BEACON',
                              'ARISS',
                              'RFONLY',
                              'NOGATE')
                # regex matching all WIDE paths like WIDE1, WIDE 1-1, WIDE2-2 etc
                wide_regex = "^WIDE(\b|([0-9]-[0-9])|[0-9])"
                # determine if the packet was digipeated by making a list of hops that dont
                # match known "path" hop types
                self.hops_path = [h for h in hops_string.split(',') if h not in path_types
                                  and re.fullmatch(wide_regex, h) is None]
                self.hops_count = len(self.hops_path)
            except IndexError:
                pass
            self._parse_coordinates(data_string)
        except IndexError:
            logging.error("Packet less than expected length")

    def _parse_packet_kiss(self, raw_packet: bytes):
        """Parse KISS-format packet bytes"""
        # TODO: finish KISS parsing
        try:
            if hex(raw_packet[0]) != "0x0":
                raise ValueError('Not a data frame?')

            self.call_to = ''.join([chr(b >> 1) for b in raw_packet[1:7]]).strip()
            self.call_from = ''.join([chr(b >> 1) for b in raw_packet[8:14]]).strip()

            try:
                split_packet = raw_packet[15:].split(b'\x03\xf0')
                path_bytes, data_bytes = split_packet[0], split_packet[1]
            except IndexError:
                # If the packet cannot be split by b'\x03\xf0' and raises an IndexError,
                # it is not a UI frame and therefore not an APRS packet
                pass
            else:
                self.frame_type = 'U'
                path_string = ''.join([chr(b >> 1) for b in path_bytes])
                path_types = ('RELAY',
                              'ECHO',
                              'TRACE',
                              'GATE',
                              'BEACON',
                              'ARISS',
                              'RFONLY',
                              'NOGATE')
                # regex matching all WIDE paths like WIDE1, WIDE 1 1, WIDE2-2 etc
                wide_regex = "^WIDE(\b|([0-9] [0-9])|[0-9])"
                # Parse hops list
                # This won't parse the hops list in headers that UI-View creates, and possibly
                # some other non-standard header formats as well
                self.hops_path = [h.strip() for h in re.split('[pqrstuwz]', path_string)
                                  if len(h.strip()) > 0
                                  and h.strip() not in path_types
                                  and re.fullmatch(wide_regex, h.strip()) is None]
                self.hops_count = len(self.hops_path)
                data_string = data_bytes.decode("ascii", errors="replace")
                logging.debug(f"Parsing data field: {repr(data_string)}")
                self._parse_coordinates(data_string)
                self.len_data = len(data_bytes)
        except IndexError:
            logging.error("Packet less than expected length")

    def _parse_info_field(self, info_field: bytes):
        logging.debug(f"Parsing info field: {repr(info_field)}")
        field_decoders = {b"\x1c": self._mic_e,
                          "b\x1d": self._mic_e,
                          "b'": self._mic_e,
                          "b`": self._mic_e,
                          "b!": self._position,
                          "b/": self._position,
                          "b=": self._position,
                          "b@": self._position,}

        data_type_byte = info_field[0]
        try:
            field_decoders[data_type_byte]()
        except KeyError:
            pass

    # The following functions set packet data type and perform some parsing based on the data type
    # identifier byte in the information field of the packet.
    def _mic_e(self):
        self.data_type = "Mic-E"
        # TODO: parse coordinates from Mic-E format

    def _weather(self):
        self.data_type = "Weather"

    def _position(self):
        self.data_type = "Position"

    def _message(self):
        self.data_type = "Message"