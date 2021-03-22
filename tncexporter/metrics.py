"""
This module defines the prometheus metrics to be exported.

All metrics ending with RECENT record a total over the time span set in the "summary_interval"
parameter of tncexporter.
"""
from aioprometheus import Counter, Gauge, Summary

# Metrics tracking counts of frames received/decoded or transmitted
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
PACKET_DISTANCE = Summary("frame_distance",
                          "Distance of received position packets from TNC (digipeated and RF)")
RF_PACKET_DISTANCE = Summary("rf_frame_distance",
                             "Distance of received position packets from TNC (RF only)")
MAX_DISTANCE_RECENT = Gauge("max_range_recent",
                            "Maximum range of position frames received over last time period")

# Metrics breaking down frame RX/TX activity by type or content
FRAME_RX_UI = Counter("frame_rx_ui",
                      "Number of monitored unproto (UI) frames received")
FRAME_RX_S = Counter("frame_rx_s",
                     "Number of monitored S/U frames received")
FRAME_RX_I = Counter("frame_rx_i",
                     "Number of monitored I frames received")
