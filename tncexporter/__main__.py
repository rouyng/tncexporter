"""
Export TNC metrics using prometheus.
"""

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
        help="URL and port for the TNC's AGWPE TCP/IP interface. Default is http://localhost:8000",
    )
    parser.add_argument(
        "--host",
        metavar="<exporter host>",
        type=str,
        default="0.0.0.0",
        help="The IP address to expose collected metrics from. Default is 0.0.0.0 (all interfaces).",
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
        default=30,
        help="The number of seconds between updates of TNC metrics. This determines the rate at "
             "which the prometheus client exposes new metrics and calculates summary metrics."
             " Default is 30 seconds. Changing this may affect how metrics appear on your "
             "grafana dashboard.",
    )
    parser.add_argument(
        "--latitude",
        metavar="<tnc latitude>",
        type=float,
        default=None,
        help="The latitude of the TNC position in decimal format. North latitudes are positive,"
             "south are negative. If this is empty, the exporter will not calculate the relative"
             " distance of position packets."
    )
    parser.add_argument(
        "--longitude",
        metavar="<tnc longitude>",
        type=float,
        default=None,
        help="The longitude of the TNC position in decimal format. East longitudes are positive, "
             "west are negative. If this is empty, the exporter will not calculate the relative"
             " distance of position packets."
    )
    parser.add_argument(
        "--debug", action="store_true", default=False, help="Print debug messages to stdout"
    )
    parser.add_argument(
        "--quiet", action="store_true", default=False, help="Only print error messages to stdout"
    )

    args = parser.parse_args()

    # set logging message verbosity
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)s: %(asctime)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S')
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR,
                            format='%(levelname)s: %(asctime)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(levelname)s: %(asctime)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S')

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
        receiver_location=location
    )
    try:
        # start metrics server and listener
        loop.run_until_complete(exp.start())
    except KeyboardInterrupt:
        pass
    else:
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
