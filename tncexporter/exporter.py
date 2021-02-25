"""
This module provides the exporter functionality.

process_packets is called from the main application loop

"""

from metrics import PACKET_RX, PACKET_TX, PACKET_DISTANCE
from math import asin, cos, sin, sqrt, radians

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


def process_packets(packet_listener: object, tnc_latlon: tuple):
    """
    Function that processes packets collected by the TNC API listener and adjusts metrics.
    :param packet_listener: a Listener object (see listener.py)
    :param tnc_latlon: a tuple defining (lat, lon) of the TNC in decimal degrees
    """
    for packet in packet_listener.packets:
        if True:
            # if a packet is received and decoded, increment PACKET_RX metric
            PACKET_RX.inc(packets_rx)
            distance_from_tnc = haversine_distance()
            PACKET_DISTANCE.observe(distance_from_tnc)
        else:
            # if a packet is transmitted, increment PACKET_TX
            PACKET_TX.inc(packets_tx)
