"""
Export TNC metrics using prometheus.
"""

from prometheus_client import start_http_server
import time
import argparse
import logging
import asyncio
from .exporter import TNCExporter


def main():
    """Run prometheus exporter"""
    # set up command-line argument parser
    parser = argparse.ArgumentParser(description='Prometheus exporter for TNC metrics')
    parser.add_argument(
        "--tnc-url",
        metavar="<TNC url and port>",
        type=str,
        dest="tnc_url",
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
        "--update-interval",
        metavar="<stats data refresh interval>",
        type=int,
        dest="update_interval",
        default=60,
        help="The number of seconds between updates of TNC metrics. This determines the rate at "
             "which the prometheus client exposes new metrics. Default is 60 seconds",
    )
    parser.add_argument(
        "--summary-interval",
        metavar="<summary metrics interval>",
        type=int,
        dest="summary_interval",
        default=300,
        help="The number of seconds over which to calculate recent activity summary metrics. "
             "Metrics that end with _recent are affected by this parameter. Default is 300 seconds"
             " (5 minutes)",
    )
    parser.add_argument(
        "--latitude",
        metavar="<tnc latitude>",
        type=float,
        default=None,
        help="The latitude of the TNC position in decimal format. North latitudes are positive,"
             "south are negative."
    )
    parser.add_argument(
        "--longitude",
        metavar="<receiver longitude>",
        type=float,
        default=None,
        help="The longitude of the TNC position in decimal format. East longitudes are positive, "
             "west are negative.",
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

    location = None
    if args.latitude and args.longitude:
        try:
            location = (float(args.latitude), float(args.longitude))
            logging.debug(f"TNC location set at {location}")
        except ValueError:
            logging.warning("Error interpreting latitude/longitude values of TNC. Distance metrics"
                            "will not be exported.")
    else:
        logging.warning("Missing latitude/longitude values. Distance metrics will not be exported.")

    loop = asyncio.get_event_loop()
    exp = TNCExporter(
        tnc_url=args.tnc_url,
        host=args.host,
        port=args.port,
        stats_interval=args.update_interval,
        summary_interval=args.summary_interval,
        receiver_location=location
    )
    loop.run_until_complete(exp.start())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(exp.stop())
    loop.stop()
    loop.close()


if __name__ == "__main__":
    main()
