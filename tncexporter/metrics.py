"""
This module defines the prometheus metrics to be exported.

All metrics ending with RECENT record a total over the time span set in the "summary_interval"
parameter of tncexporter.
"""
from aioprometheus import Counter, Gauge, Summary, Histogram

# Metrics tracking counts of frames received/decoded or transmitted
# PACKET_RX labels:
# 'ax_25_frame_type' : "U", "I", "S" for AX.25 frame types
# 'path' : "Digi" for digipeated packets (hops > 0), "Simplex" for simplex packets (0 hops)
# 'from_cs' : Originating callsign
PACKET_RX = Counter("tnc_packet_rx",
                    "Number of packets received and decoded")
PACKET_TX = Counter("tnc_packet_tx",
                    "Number of packets transmitted")

RX_PACKET_SIZE = Histogram("tnc_rx_packet_size",
                        "Length in bytes of data field in received packets",
                           buckets=[0, 50, 100, 150, 200, 250, 300, 350])

TX_PACKET_SIZE = Histogram("tnc_tx_packet_size",
                        "Length in bytes of data field in transmitted packets",
                           buckets=[0, 50, 100, 150, 200, 250, 300, 350])

# Summary metrics tracking distances of received frames. Only calculated for frames that report
# position data (APRS). Not currently used in dashboard
PACKET_DISTANCE = Summary("tnc_packet_distance",
                          "Distance in meters of received position packets from TNC "
                          "(digipeated and simplex)")
RF_PACKET_DISTANCE = Summary("tnc_rf_packet_distance",
                             "Distance in meters of received position packets from TNC (simplex only)")

# Aggregate metrics, calculated from all packets collected across the interval
# defined by update_interval
MAX_DISTANCE_RECENT = Gauge("tnc_max_range_recent",
                            "Maximum range in meters of position frames received over last time "
                            "period. Includes digipeated frames")
MAX_RF_DISTANCE_RECENT = Gauge("tnc_max_rf_range_recent",
                            "Maximum range in meters of non-digipeated position frames received over last time "
                            "period")
PACKET_RX_RECENT_PATH = Gauge("tnc_packet_rx_recent_path",
                         "Number of packets received over last time period, labeled by path type")
PACKET_RX_RECENT_FRAME = Gauge("tnc_packet_rx_recent_frame",
                         "Number of packets received over last time period, labeled by AX.25 frame type")
PACKET_TX_RECENT_PATH = Gauge("tnc_packet_tx_recent_path",
                         "Number of packets transmitted over last time period, labeled by path type")

