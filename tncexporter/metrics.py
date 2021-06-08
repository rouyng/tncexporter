"""
This module defines the prometheus metrics to be exported.

All metrics ending with RECENT record a total over the time span set in the "summary_interval"
parameter of tncexporter.
"""
from aioprometheus import Counter, Gauge, Summary

# Metrics tracking counts of frames received/decoded or transmitted
# PACKET_RX labels:
# 'ax_25_frame_type' : "U", "I", "S" for AX.25 frame types
# 'path' : "Digi" for digipeated packets (hops > 0), "Simplex" for simplex packets (0 hops)
PACKET_RX = Counter("packet_rx",
                    "Number of packets received and decoded")
PACKET_TX = Counter("packet_tx",
                    "Number of packets transmitted")
PACKET_RX_RECENT = Gauge("packet_rx_recent",
                         "Number of packets received over last time period")
PACKET_TX_RECENT = Gauge("packet_tx_recent",
                         "Number of packets transmitted over last time period")

# Metrics tracking distances of received frames. Only calculated for frames that report
# position data (APRS)
PACKET_DISTANCE = Summary("packet_distance",
                          "Distance in meters of received position packets from TNC "
                          "(digipeated and RF)")
RF_PACKET_DISTANCE = Summary("rf_packet_distance",
                             "Distance in meters of received position packets from TNC (RF only)")
MAX_DISTANCE_RECENT = Gauge("max_range_recent",
                            "Maximum range in meters of position frames received over last time "
                            "period")
