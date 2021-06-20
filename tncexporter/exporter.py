"""
This module provides the exporter functionality.

process_packets is called from the main application loop

"""
import sys

from .metrics import PACKET_RX, PACKET_TX, PACKET_DISTANCE,\
    RF_PACKET_DISTANCE, MAX_DISTANCE_RECENT, PACKET_RX_RECENT, PACKET_TX_RECENT
from math import asin, cos, sin, sqrt, radians
from typing import TypedDict
import asyncio
import datetime
import functools
import logging
import re
from .listener import Listener
from asyncio.events import AbstractEventLoop
from aioprometheus import Service

logger = logging.getLogger(__name__)


class PacketInfo(TypedDict):
    """Typed dictionary for defining AX.25 packet metadata"""
    frame_type: str  # type of frame (U, I, S, T, other)
    data_len: int  # length of data in packet (inclusive of 36 byte header)
    call_from: str  # originating callsign
    call_to: str  # destination callsign
    timestamp: datetime.time  # timestamp of when packet was received by TNC
    lat_lon: tuple  # tuple containing two floats representing latitude and longitude
    hops_count: int  # number of hops. Non-digipeated packets should have 0
    hops_path: list  # list of hop callsigns


class TNCExporter:
    def __init__(
            self,
            tnc_url: str,
            host: str = None,
            port: int = 9105,
            stats_interval: int = 60,
            summary_interval: int = 60,
            receiver_location: tuple = None,
            loop: AbstractEventLoop = None) -> None:
        try:
            self.listener = Listener(tnc_url)
        except ConnectionRefusedError:
            logging.error("Could not create TNC listener")
            sys.exit()
        else:
            self.loop = loop or asyncio.get_event_loop()
            self.host = host
            self.port = port
            self.stats_interval = datetime.timedelta(seconds=stats_interval)
            self.summary_interval = datetime.timedelta(seconds=summary_interval)
            self.location = receiver_location
            self.metrics_task = None
            self.listener_task = None
            self.server = Service()
            self.register_metrics((PACKET_RX,
                                   PACKET_TX,
                                   PACKET_DISTANCE,
                                   RF_PACKET_DISTANCE,
                                   MAX_DISTANCE_RECENT,
                                   PACKET_RX_RECENT,
                                   PACKET_TX_RECENT
                                   ))

    def register_metrics(self, metrics_list: tuple):
        """Register metrics  with aioprometheus service"""
        for m in metrics_list:
            self.server.register(m)

    async def start(self) -> None:
        """ Start the monitor """
        await self.server.start(addr=self.host, port=self.port)
        logger.info(f"serving TNC prometheus metrics on: {self.server.metrics_url}")
        self.metrics_task = asyncio.create_task(self.metric_updater())
        self.listener_task = asyncio.create_task(self.listener.receive_packets())

    async def stop(self) -> None:
        """ Stop the monitor """
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass
            self.metrics_task = None
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
            self.listener_task = None
        await self.server.stop()  # stop prometheus server
        self.listener.disconnect()  # disconnect listener from TNC

    @staticmethod
    def haversine_distance(
            pos1: tuple,
            pos2: tuple,
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
        :param pos1: a tuple defining (lat, lon) in decimal degrees
        :param pos2: a tuple defining (lat, lon) in decimal degrees
        :param radius: radius of sphere in meters.
        :returns: distance between two points in meters.
        :rtype: float
        """
        lat1, lon1, lat2, lon2 = [radians(x) for x in (*pos1, *pos2)]

        hav = (
                sin((lat2 - lat1) / 2.0) ** 2
                + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2.0) ** 2
        )
        distance = 2 * radius * asin(sqrt(hav))
        return distance

    @staticmethod
    def parse_packet(raw_packet):
        """Parse packet bytestring, create a PacketInfo object
        :param raw_packet: packet bytestrings
        :returns: Typed dictionary containing metadata
        :rtype: PacketInfo"""
        len_data = int.from_bytes(raw_packet[28:32], signed=False, byteorder="little")
        frame_type = chr(raw_packet[4]).upper()
        try:
            call_from = raw_packet[8:18].strip(b'\x00').decode("ascii")
        except UnicodeDecodeError:
            call_from = None
            logging.debug(f"Unicode error when decoding: {raw_packet[8:18]}")
        try:
            call_to = raw_packet[18:28].strip(b'\x00').decode("ascii")
        except UnicodeDecodeError:
            call_to = None
            logging.debug(f"Unicode error when decoding: {raw_packet[18:28]}")

        timestamp = None
        latitude = None
        longitude = None
        hops = []
        try:
            data_string = raw_packet[36:].strip(b'\x00').decode("ascii")
            logging.debug("Parsing data from the following string:")
            logging.debug(data_string)
            # parse timestamp
            time_match = re.search("[0-2][0-9]:[0-5][0-9]:[0-5][0-9]", data_string)
            if time_match is not None:
                try:
                    raw_hour = time_match.group()[0:2]
                    raw_min = time_match.group()[3:5]
                    raw_sec = time_match.group()[6:8]
                    timestamp = datetime.time(hour=int(raw_hour),
                                              minute=int(raw_min),
                                              second=int(raw_sec))
                except TypeError:
                    pass
            try:
                # parse list of hops
                hops_string = re.findall("(?:Via )(.*?)(?: <)", data_string)[0]
                # tuple of non-WIDE path types that don't represent hops through a digipeater
                # TODO: research additional paths that may appear in packets?
                path_types = ('RELAY',
                              'BEACON',
                              'ARISS',
                              'RFONLY',
                              'NOGATE')
                # regex matching all WIDE paths like WIDE1, WIDE 1-1, WIDE2-2 etc
                wide_regex = "^WIDE(\b|([0-9]-[0-9])|[0-9])"
                # determine if the packet was digipeated by making a list of hops that dont
                # match known "path" hop types
                hops = [h for h in hops_string.split(',') if h not in path_types
                        and re.fullmatch(wide_regex, h) is None]
            except IndexError:
                pass
            try:
                # parse latitude and longitude from position packets
                latlon_regex = r"([0-9][0-9][0-9][0-9]\.[0-9][0-9])(?:[0-9]|,){0,5}(N|S).{0,2}" \
                               r"([0-1][0-9][0-9][0-9][0-9]\.[0-9][0-9])(?:[0-9]|,){0,5}(E|W)"
                latlon_match = re.search(latlon_regex, data_string)
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
                else:
                    logging.debug("No latitude/longitude values found in packet")
            except (IndexError, ValueError):
                pass

        except UnicodeDecodeError:
            logging.error("Error decoding bytes into unicode")

        decoded_info = PacketInfo(
            frame_type=frame_type,
            data_len=len_data,
            call_from=call_from,
            call_to=call_to,
            timestamp=timestamp,
            hops_count=len(hops),
            hops_path=hops,
            lat_lon=(latitude, longitude)
        )
        logging.debug(f"Decoded packet: {decoded_info}")
        return decoded_info

    async def metric_updater(self):
        """Asynchronous coroutine function that reads the queue of received packets and calls
        packet_metrics on each packet in the queue. Runs on an interval defined by the update
        interval set when starting the exporter."""

        while True:
            packets_to_summarize = []
            start = datetime.datetime.now()
            try:
                # Only try to get packet bytestrings from the queue if it is not empty
                while not self.listener.packet_queue.empty():
                    packet = await self.listener.packet_queue.get()
                    parsed = self.parse_packet(packet)
                    self.packet_metrics(parsed)
                    logging.debug(f"Updated metrics for packet received from TNC")
                    packets_to_summarize.append(parsed)
                    self.listener.packet_queue.task_done()
            except Exception:
                logging.exception("Error processing packet into metrics: ")
            try:
                self.summary_metrics(packets_to_summarize)
            except Exception:
                logging.exception("Error processing summary metrics from packets: ")
            # await end of sleep cycle to update metrics, defined by update-interval parameter
            end = datetime.datetime.now()
            wait_seconds = (start + self.stats_interval - end).total_seconds()
            await asyncio.sleep(wait_seconds)

    def packet_metrics(self, packet_info: PacketInfo):
        """
        Function that processes individual packet metadata from a PacketInfo object
         and updates Prometheus metrics.

        :param packet_info: a PacketInfo object containing packet metadata
        :param tnc_latlon: a tuple defining (lat, lon) of the TNC in decimal degrees
        """
        path_type = "Digi" if packet_info['hops_count'] > 0 else "Simplex"
        if packet_info['frame_type'] == 'T':
            # if a packet is transmitted, increment PACKET_TX
            # TODO: more informative labels
            PACKET_TX.inc({'path': path_type})
        else:
            # if a packet is received and decoded, increment PACKET_RX metric
            PACKET_RX.inc({'ax25_frame_type': packet_info['frame_type'],
                           'path': path_type,
                           'from_cs': packet_info['call_from']})
            if all([v is not None for v in packet_info['lat_lon']]) and self.location is not None:
                # calculate distance between TNC location and packet's reported lat/lon
                distance_from_tnc = self.haversine_distance(pos1=self.location,
                                                            pos2=packet_info['lat_lon'])
                # Update PACKET_DISTANCE for all received packets with lat/lon info, including
                # ones received by digipeating
                PACKET_DISTANCE.observe({'type': 'unknown'}, distance_from_tnc)
                if packet_info['hops_count'] == 0:
                    # No hops means the packet was received via RF, so update RF_PACKET_DISTANCE
                    RF_PACKET_DISTANCE.observe({'type': 'unknown'}, distance_from_tnc)

    def summary_metrics(self, packets: list[PacketInfo]):
        """
        Function that processes multiple PacketInfo object
         and updates Prometheus metrics based on aggregate measurements across the update interval.

        :param packets: a list of PacketInfo objects containing packet metadata
        :param tnc_latlon: a tuple defining (lat, lon) of the TNC in decimal degrees
        """
        packets_rx_count = 0
        packets_tx_count = 0
        max_rf_distance = 0
        max_digi_distance = 0
        if len(packets) > 0:
            packets_rx = [p for p in packets if p['frame_type'] != 'T']
            packets_rx_count = len(packets_rx)
            packets_tx_count = len([p for p in packets if p['frame_type'] == 'T'])
            if all([w is not None for w in self.location]):
                # ValueError is raised if max arg is empty
                try:
                    max_rf_distance = max([self.haversine_distance(self.location, p['lat_lon']) for p
                                           in packets_rx if all([w is not None for w in p['lat_lon']])
                                           and p['hops_count'] == 0])
                except ValueError:
                    pass
                try:
                    max_digi_distance = max([self.haversine_distance(self.location, p['lat_lon']) for p
                                            in packets_rx if all([w is not None for w in p['lat_lon']])
                                            and p['hops_count'] > 0])
                except ValueError:
                    pass

        # Update summary metrics for last update interval

        MAX_DISTANCE_RECENT.set({'interval': self.stats_interval.seconds, 'path': 'Simplex'},
                                max_rf_distance)
        MAX_DISTANCE_RECENT.set({'interval': self.stats_interval.seconds, 'path': 'Digi'},
                                max_digi_distance)
        PACKET_RX_RECENT.set({'interval': self.stats_interval.seconds}, packets_rx_count)
        PACKET_TX_RECENT.set({'interval': self.stats_interval.seconds}, packets_tx_count)
        logging.info("Updated summary metrics")
