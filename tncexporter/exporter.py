"""
This module provides the exporter functionality.

process_packets is called from the main application loop

"""

from .metrics import PACKET_RX, PACKET_TX, PACKET_DISTANCE, RX_PACKET_SIZE, TX_PACKET_SIZE, \
    RF_PACKET_DISTANCE, MAX_DISTANCE_RECENT, PACKET_RX_RECENT_PATH, PACKET_RX_RECENT_FRAME, \
    PACKET_TX_RECENT_PATH
import asyncio
import datetime
import logging
from .listener import Listener
from asyncio.events import AbstractEventLoop
from aioprometheus import Service
from .parser import PacketInfo
from typing import List

logger = logging.getLogger(__name__)


class TNCExporter:
    def __init__(
            self,
            tnc_url: str,
            host: str = None,
            port: int = 9105,
            kiss_mode: bool = False,
            stats_interval: int = 60,
            receiver_location: tuple = None,
            loop: AbstractEventLoop = None) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.kiss_mode = kiss_mode
        self.tnc_url = tnc_url
        self.host = host
        self.port = port
        self.stats_interval = datetime.timedelta(seconds=stats_interval)
        self.location = receiver_location
        self.listener = None
        self.metrics_task = None
        self.listener_task = None
        self.server = Service()
        self.register_metrics((PACKET_RX,
                               PACKET_TX,
                               RX_PACKET_SIZE,
                               TX_PACKET_SIZE,
                               PACKET_DISTANCE,
                               RF_PACKET_DISTANCE,
                               MAX_DISTANCE_RECENT,
                               PACKET_RX_RECENT_PATH,
                               PACKET_RX_RECENT_FRAME,
                               PACKET_TX_RECENT_PATH
                               ))

    def register_metrics(self, metrics_list: tuple):
        """Register metrics  with aioprometheus service"""
        for m in metrics_list:
            self.server.register(m)

    async def start(self) -> None:
        """ Start the TNC listener and prometheus service, create async tasks"""
        # start TNC listener and attempt to connect to TNC
        self.listener = Listener(tnc_url=self.tnc_url, kiss_mode=self.kiss_mode)
        # start prometheus metrics server
        await self.server.start(addr=self.host, port=self.port)
        logger.info(f"Serving TNC prometheus metrics on: {self.server.metrics_url}")
        # create long-running asyncio tasks to listen for packets and update metrics
        self.metrics_task = asyncio.create_task(self.metric_updater())
        self.listener_task = asyncio.create_task(self.listener.receive_packets())

    async def stop(self) -> None:
        """ Stop the monitor """
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass
            self.metrics_task = None
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
            self.listener_task = None
        await self.server.stop()  # stop prometheus server
        self.listener.disconnect()  # disconnect listener from TNC

    async def metric_updater(self):
        """Asynchronous coroutine function that reads the queue of received packets and calls
        packet_metrics on each packet in the queue. Runs on an interval defined by the update
        interval set when starting the exporter."""

        while True:
            packets_to_summarize = []
            start = datetime.datetime.now()
            try:
                # Only try to get packet bytestrings from the queue if it is not empty
                while not self.listener.packet_queue.empty():
                    packet = await self.listener.packet_queue.get()
                    # check if KISS mode is turned on, otherwise use AGW packet parser
                    if self.kiss_mode:
                        parsed = PacketInfo(packet, kiss=True)
                        logging.debug(f"Parsed KISS packet: {parsed.__dict__}")
                    else:
                        parsed = PacketInfo(packet, kiss=False)
                        logging.debug(f"Parsed AGW packet: {parsed.__dict__}")

                    self.packet_metrics(parsed)
                    logging.debug("Updated metrics for packet received from TNC")
                    packets_to_summarize.append(parsed)
                    self.listener.packet_queue.task_done()
            except Exception:
                logging.exception("Error processing packet into metrics: ")
            try:
                self.summary_metrics(packets_to_summarize)
            except Exception:
                logging.exception("Error processing summary metrics from packets: ")
            # await end of sleep cycle to update metrics, defined by update-interval parameter
            logging.info(f"Updated metrics for {len(packets_to_summarize)} packets")
            end = datetime.datetime.now()
            wait_seconds = (start + self.stats_interval - end).total_seconds()
            await asyncio.sleep(wait_seconds)

    def packet_metrics(self, packet_info: PacketInfo):
        """
        Function that processes individual packet metadata from a PacketInfo object
         and updates Prometheus metrics.

        :param packet_info: a PacketInfo object containing packet metadata
        """
        path_type = "Digipeated" if packet_info.hops_count > 0 else "Simplex"

        if packet_info.frame_type == 'T':
            # if a packet is transmitted, increment PACKET_TX
            PACKET_TX.inc({'path': path_type})
            TX_PACKET_SIZE.observe({}, packet_info.len_data)
        else:
            RX_PACKET_SIZE.observe({}, packet_info.len_data)
            # if a packet is received and decoded, increment PACKET_RX metric
            PACKET_RX.inc({'ax25_frame_type': packet_info.frame_type,
                           'path': path_type,
                           'from_cs': packet_info.call_from})
            if all([v is not None for v in packet_info.lat_lon]) \
                    and all([w is not None for w in self.location]):
                # calculate distance between TNC location and packet's reported lat/lon
                distance_from_tnc = packet_info.haversine_distance(tnc_pos=self.location)
                # Update PACKET_DISTANCE for all received packets with lat/lon info, including
                # ones received by digipeating
                PACKET_DISTANCE.observe({'type': 'unknown'}, distance_from_tnc)
                if packet_info.hops_count == 0:
                    # No hops means the packet was received via RF, so update RF_PACKET_DISTANCE
                    RF_PACKET_DISTANCE.observe({'type': 'unknown'}, distance_from_tnc)

    def summary_metrics(self, packets: List[PacketInfo]):
        """
        Function that processes multiple PacketInfo object
         and updates Prometheus metrics based on aggregate measurements across the update interval.

        :param packets: a list of PacketInfo objects containing packet metadata
        """
        packets_rx_count: int = 0
        packets_rx_u_count: int = 0
        packets_rx_i_count: int = 0
        packets_rx_s_count: int = 0
        packets_rx_unknown_count: int = 0
        packets_rx_digi_count: int = 0
        packets_rx_simplex_count: int = 0
        packets_tx_count: int = 0
        packets_tx_digi_count: int = 0
        packets_tx_simplex_count: int = 0
        max_rf_distance: float = 0
        max_digi_distance: float = 0
        if len(packets) > 0:
            logging.debug(f"Calculating summary metrics for {len(packets)} packets")
            packets_rx = [p for p in packets if p.frame_type != 'T']
            packets_tx = [p for p in packets if p.frame_type == 'T']
            packets_rx_count = len(packets_rx)
            packets_rx_u_count = len([p for p in packets_rx if p.frame_type == 'U'])
            packets_rx_i_count = len([p for p in packets_rx if p.frame_type == 'I'])
            packets_rx_s_count = len([p for p in packets_rx if p.frame_type == 'S'])
            packets_rx_unknown_count = len([p for p in packets_rx if p.frame_type == 'Unknown'])
            packets_rx_digi_count = len([p for p in packets_rx if p.hops_count > 0])
            packets_rx_simplex_count = len([p for p in packets_rx if p.hops_count == 0])
            packets_tx_count = len(packets_tx)
            packets_tx_digi_count = len([p for p in packets_tx if p.hops_count > 0])
            packets_tx_simplex_count = len([p for p in packets_tx if p.hops_count == 0])

            if all([w is not None for w in self.location]):
                # ValueError is raised if max arg is empty
                try:
                    max_rf_distance = max(
                        [p.haversine_distance(tnc_pos=self.location) for p
                         in packets_rx if all([w is not None for w in p.lat_lon])
                         and p.hops_count == 0])
                except ValueError:
                    pass
                try:
                    max_digi_distance = max(
                        [p.haversine_distance(tnc_pos=self.location) for p
                         in packets_rx if all([w is not None for w in p.lat_lon])
                         and p.hops_count > 0])
                except ValueError:
                    pass

        # Update summary metrics for last update interval
        MAX_DISTANCE_RECENT.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                 'path': 'Simplex'},
                                max_rf_distance)
        MAX_DISTANCE_RECENT.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                 'path': 'Digipeated'},
                                max_digi_distance)
        # Set count of all packets received, including all paths and frame types
        PACKET_RX_RECENT_FRAME.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                    'path': 'All',
                                    'frame_type': 'All'},
                                   packets_rx_count)
        # Set count of U frames received
        PACKET_RX_RECENT_FRAME.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                    'path': 'All',
                                    'frame_type': 'U'},
                                   packets_rx_u_count)
        # Set count of I frames received
        PACKET_RX_RECENT_FRAME.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                    'path': 'All',
                                    'frame_type': 'I'},
                                   packets_rx_i_count)
        # Set count of S frames received
        PACKET_RX_RECENT_FRAME.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                    'path': 'All',
                                    'frame_type': 'S'},
                                   packets_rx_s_count)
        # Set count of unknown type frames received
        PACKET_RX_RECENT_FRAME.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                    'path': 'All',
                                    'frame_type': 'Unknown'},
                                   packets_rx_unknown_count)
        # Set count of simplex packets received, including all frame types
        PACKET_RX_RECENT_PATH.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                   'path': 'All',
                                   'frame_type': 'All'},
                                  packets_rx_count)
        # Set count of simplex packets received, including all frame types
        PACKET_RX_RECENT_PATH.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                   'path': 'Simplex',
                                   'frame_type': 'All'},
                                  packets_rx_simplex_count)
        # Set count of digipeated packets received, including all frame types
        PACKET_RX_RECENT_PATH.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                   'path': 'Digipeated',
                                   'frame_type': 'All'},
                                  packets_rx_digi_count)
        PACKET_TX_RECENT_PATH.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                   'path': 'All',
                                   'frame_type': 'All'},
                                  packets_tx_count)
        # Set count of simplex packets transmitted, including all frame types
        PACKET_TX_RECENT_PATH.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                   'path': 'Simplex',
                                   'frame_type': 'All'},
                                  packets_tx_simplex_count)
        # Set count of digipeated packets transmitted, including all frame types
        PACKET_TX_RECENT_PATH.set({'interval': f'Last {self.stats_interval.seconds} seconds',
                                   'path': 'Digipeated',
                                   'frame_type': 'All'},
                                  packets_tx_digi_count)
