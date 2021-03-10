"""
This module provides the exporter functionality.

process_packets is called from the main application loop

"""

from .metrics import PACKET_RX, PACKET_TX, PACKET_DISTANCE, RF_PACKET_DISTANCE
from math import asin, cos, sin, sqrt, radians
from typing import TypedDict
import datetime
import logging


class PacketInfo(TypedDict):
    """Typed dictionary for defining AX.25 packet metadata"""
    frame_type: str  # type of frame (U, I, S, T, other)
    data_len: int  # length of data in packet (inclusive of 36 byte header)
    call_from: str  # originating callsign
    call_to: str  # destination callsign
    timestamp: datetime.datetime  # timestamp of when packet was received by TNC
    lat_lon: tuple  # tuple containing two floats representing latitude and longitude


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


def decode_packet(raw_packet):
    """Decode packet bytestring, create a PacketInfo object
    :param raw_packet: packet bytestrings
    :returns: Typed dictionary containing metadata
    :rtype: PacketInfo"""
    len_data = int.from_bytes(raw_packet[30:34], signed=False, byteorder="little", )
    frame_type = chr(raw_packet[4])
    try:
        call_from = raw_packet[8:18].decode("utf-8").strip('\x00')
    except UnicodeDecodeError:
        call_from = None
        logging.debug(f"Unicode error when decoding: {raw_packet[8:18]}")
    try:
        call_to = raw_packet[18:28].decode("utf-8").strip('\x00')
    except UnicodeDecodeError:
        call_to = None
        logging.debug(f"Unicode error when decoding: {raw_packet[18:28]}")
    return PacketInfo(
        frame_type=frame_type,
        data_len=len_data,
        call_from=call_from,
        call_to=call_to
    )


def update_metrics(packet_info: PacketInfo, tnc_latlon: tuple):
    """
    Function that processes packet metadata and updates Prometheus metrics.

    :param packet_info: a list of PacketInfo objects containing packet metadata
    :param tnc_latlon: a tuple defining (lat, lon) of the TNC in decimal degrees
    """
    if packet_info['frame_type'] == 't':
        # if a packet is transmitted, increment PACKET_TX
        PACKET_TX.inc()
    else:
        # if a packet is received and decoded, increment PACKET_RX metric
        PACKET_RX.inc()
        if packet_info['lat_lon']:
            # calculate distance between TNC location and packet's reported lat/lon
            distance_from_tnc = haversine_distance(pos1=tnc_latlon, pos2=packet_info['lat_lon'])
            PACKET_DISTANCE.observe(distance_from_tnc)
            # TODO: determine if packet was digipeated to increment RF_PACKET_DISTANCE

