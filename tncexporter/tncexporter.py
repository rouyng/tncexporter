"""
This module orchestrates the exporter functionality.

Currently contains placeholder code from the official Prometheus client
"""

from prometheus_client import start_http_server, Summary
from metrics import PACKET_RX, PACKET_TX, PACKET_DISTANCE
import time
import argparse

# TODO: haversine distance function to calculate distance of packets from TNC


def process_packets():
    """Function that processes packets exposed by TNC API and adjusts metrics accordingly"""
    # placeholder for values obtained by processing packets captured by TCP/IP API listener
    packets_rx = 0
    packets_tx = 0
    packet_distances = []
    # update prometheus metrics
    PACKET_RX.inc(packets_rx)
    PACKET_TX.inc(packets_tx)
    for d in packet_distances:
        PACKET_DISTANCE.observe(d)


def main():
    """Run prometheus client and export TNC metrics"""
    # set up command-line argument parser
    parser = argparse.ArgumentParser(description='Prometheus exporter for TNC metrics')
    
    # Start up the http server to expose the metrics.
    # The prometheus server pulls metrics from the exporter's http server
    start_http_server(8000)

    while True:
        process_packets()
        # wait x seconds before generating metrics again
        time.sleep(60)


if __name__ == '__main__':
    main()
