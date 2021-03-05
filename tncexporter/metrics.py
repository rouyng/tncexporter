"""
This module defines the prometheus metrics to be exported
"""
from prometheus_client import Counter, Histogram, Summary

PACKET_RX = Counter("packet_rx",
                    "Number of packets received and decoded")
PACKET_TX = Counter("packet_tx",
                    "Number of packets transmitted")
PACKET_DISTANCE = Histogram("packet_distance",
                            "Distance of packets from TNC (digipeated and RF)")
RF_PACKET_DISTANCE = Histogram("rf_packet_distance",
                               "Distance of received packets from TNC (RF only)")

