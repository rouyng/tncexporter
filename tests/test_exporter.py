"""
Unit tests for exporter.py module. Uses pytest framework.

Many packet examples used in test cases were produced by direwolf decoding packets recorded on
WA8LMF's TNC Test CD. http://wa8lmf.net/TNCtest/. Others were modified from this data, created
specifically for use in testing, or decoded from one of the following WebSDRs:
https://websdr3.sdrutah.org
http://dlwis-websdr.ham-radio-op.net:8901/
http://appr.org.br:8901/
"""
import socket

from .context import tncexporter
import pytest
import asyncio
import os
import sys
import datetime
from pytest_mock import mocker
from typing import List, Tuple
import requests


# TODO: write integration tests
# FIXME: none of this works currently

# One option is to create an async AGWServer object that operates like an actual TNC
# and run TNC exporter as an async subprocess, connecting to AGWServer over TCP.
# A third async couroutine would then run the tests by making requests to the metrics endpoint.

# Another option is to make a wrapper for the tncexporter.Exporter class that will run an event loop
# with the addition of a tester coroutine. Calls to socket.recv() and AbstractEventLoop.sock_recv()
# can be mocked. This is probalby the preferred approach,

class AGWServer:
    """Simulates behavior of the AGW TCP/IP interface of a TNC"""

    def __init__(self):
        # create agw server and listen for version and monitoring requests
        self.port = 8000  # port to host test server
        self.reader = None
        self.writer = None

    async def establish_connection(self):
        self.reader, self.writer = await asyncio.open_connection(host='127.0.0.1', port=self.port)
        version_request = await self.reader.read()
        print(version_request.decode())
        # FIXME: check version request is as expected, send back reply
        # FIXME: listen for monitoring request

    async def send_packets(self, packets):
        for p in packets:
            # send each packet to test client
            self.writer.write(p)
            await asyncio.sleep(0.1)


async def run(cmd):
    """asynchronously run a subprocess, useful for running tncexporter in tests"""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    start = datetime.datetime.now()
    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        return stdout.decode()
    if stderr:
        return stderr.decode()


def setup_env():
    """Setup function for running subprocesses"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsProactorEventLoopPolicy())


class ExporterTestWrapper:
    """Run exporter, listener and test_function tasks within event loop"""

    def __init__(self, test_function,
                 loop: asyncio.AbstractEventLoop,
                 mocker,
                 packets: List[bytes],
                 location: Tuple[float, float],
                 kiss_mode: bool = False,

                 ):
        self.packets = packets
        self.VERSION_REPLY = b"\x00\x00\x00\x00\x52\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                             b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                             b"\x00\x00\x00\x00"
        self.loop = loop
        # run exporter with hardcoded parameters
        exp = tncexporter.TNCExporter(
            tnc_url="http://localhost:8000",
            host="localhost",
            port=9110,
            kiss_mode=kiss_mode,
            stats_interval=1,
            receiver_location=location
        )
        try:
            mock_sock = mocker.patch('socket.socket')
            mock_sock.recv.return_value = self.VERSION_REPLY
            self.loop.run_until_complete(exp.start())

        except KeyboardInterrupt:
            pass
        else:
            try:
                mock_async_sock = mocker.patch('asyncio.AbstractEventLoop.sock_recv')
                mock_async_sock.return_value = self.packets.pop()
                self.loop.run_forever()
            # an IndexError will be raised when we have popped the last item from self.packets
            except IndexError:
                # once we exhaust the list of packets, run the tests
                test_function()
            finally:
                self.loop.run_until_complete(exp.stop())
        self.loop.stop()
        self.loop.close()


class TestExporterCreation:
    """Test startup of TNC exporter and connection to KISS and AGW interfaces"""

    def test_exporter_startup(self):
        """Test that tnc exporter runs and returns the help message. The most basic function test"""

        async def test_help_message():
            result = await run('python -m tncexporter --help')
            assert "Prometheus exporter for TNC metrics" in result
            assert "--update-interval <stats data refresh interval>" in result

        setup_env()
        asyncio.run(test_help_message())


class TestMetricUpdating:
    def test_one_packet(self, event_loop):
        agw_packets = [b'\x00\x00\x00\x00U\x00\x00\x00KF6WJS-14\x00S4PWYR\x00\x00\x00\x00X\x00\x00' \
                       b'\x00\x00\x00\x00\x00 1:Fm KF6WJS-14 To S4PWYR Via WIDE2-2 <UI pid=F0 ' \
                       b'Len=13 PF=0 >[14:32:38]\r`.a"l!^k/"6b}\r\x00 ']

        def check_conditions():
            # fetch the metrics endpoint
            metrics_response = requests.get("http://localhost:9110")
            # run tests against the text served at the metrics endpoint
            assert metrics_response.status_code == 200
            # TODO: replace these with actual tests
            assert "something" in metrics_response.text
            assert "something else" in metrics_response.text

        ExporterTestWrapper(test_function=check_conditions,
                            loop=event_loop,
                            mocker=mocker,
                            packets=agw_packets,
                            kiss_mode=False,
                            location=(None, None))
