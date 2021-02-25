"""
Export TNC metrics using prometheus.
"""

from prometheus_client import start_http_server
import time
import argparse
import logging
import exporter
import listener

"""Run prometheus client and export TNC metrics"""
# set up command-line argument parser
parser = argparse.ArgumentParser(description='Prometheus exporter for TNC metrics')
parser.add_argument(
    "--tnc-url",
    metavar="<TNC url and port>",
    type=str,
    default="http://localhost:8000",
    help="the URL for the TNC's AGWPE TCP/IP interface",
)
parser.add_argument(
    "--host",
    metavar="<exporter host>",
    type=str,
    default="0.0.0.0",
    help="The address to expose collected metrics from. Default is all interfaces.",
)
parser.add_argument(
    "--port",
    metavar="<exporter port>",
    type=int,
    default=9110,
    help="The port to expose collected metrics from. Default is 9110",
)
parser.add_argument(
    "--stats-interval",
    metavar="<stats data refresh interval>",
    type=int,
    dest="interval",
    default=60,
    help="The number of seconds between updates of TNC stats. Default is 60 seconds",
)
parser.add_argument(
    "--latitude",
    metavar="<tnc latitude>",
    type=float,
    default=None,
    help="The latitude of the TNC position",
)
parser.add_argument(
    "--longitude",
    metavar="<receiver longitude>",
    type=float,
    default=None,
    help="The longitude of the TNC position",
)
parser.add_argument(
    "--debug", action="store_true", default=False, help="Print debug output"
)

args = parser.parse_args()

# set logging message verbosity
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Start up the http server to expose the metrics.
# The prometheus server pulls metrics from the exporter's http server
start_http_server(port=args.port, addr=args.host)

while True:
    exporter.process_packets()
    # wait x seconds before generating metrics again
    time.sleep(args.interval)