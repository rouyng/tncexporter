"""
Parser functions to extract relevant data from AGW or KISS format packets
"""
import datetime
import logging
import re
from math import asin, cos, sin, sqrt, radians


class PacketInfo:
    """Object for parsing and storing AX.25 packet metadata"""

    def __init__(self, packet_bytes: bytes, kiss: bool = False):
        self.raw_bytes: bytes = packet_bytes
        logging.debug(f"Parsing packet bytes: {repr(self.raw_bytes)}")
        self.frame_type: str = "Unknown"  # type of frame (U, I, S, T, other)
        self.data_len: int = 0  # length of data in packet (inclusive of 36 byte header)
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
            tnc_pos: tuple[float, float],
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
        return distance

    def _parse_packet_agw(self, raw_packet: bytes):
        """Parse AGW-format packet bytes, create a PacketInfo object
        :param raw_packet: packet bytes
        """
        try:
            self.len_data = int.from_bytes(raw_packet[28:32], signed=False, byteorder="little")
            self.frame_type = chr(raw_packet[4]).upper()
            try:
                self.call_from = raw_packet[8:18].strip(b'\x00').decode("ascii")
            except UnicodeDecodeError:
                logging.debug(f"Unicode error when decoding: {raw_packet[8:18]}")
            try:
                self.call_to = raw_packet[18:28].strip(b'\x00').decode("ascii")
            except UnicodeDecodeError:
                logging.debug(f"Unicode error when decoding: {raw_packet[18:28]}")
            try:
                data_string = raw_packet[36:].strip(b'\x00').decode("ascii")
                logging.debug(f"Parsing data from the following string: {repr(data_string)}")
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
            except UnicodeDecodeError:
                logging.error("Error decoding bytes into unicode")
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
                self.hops_path = [h.strip() for h in re.split('[pqswz]', path_string)
                                  if len(h.strip()) > 0
                                  and h.strip() not in path_types
                                  and re.fullmatch(wide_regex, h.strip()) is None]
                self.hops_count = len(self.hops_path)
                try:
                    logging.debug(f"Parsing position from data bytes: {repr(data_bytes)}")
                    self._parse_coordinates(data_bytes.decode("ascii"))
                except UnicodeDecodeError:
                    logging.exception("Could not decode data field of packet into ascii: ")
                self.len_data = len(data_bytes)
        except IndexError:
            logging.error("Packet less than expected length")
