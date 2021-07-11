"""
Unit tests for exporter.py module. Uses pytest framework.

Many packet examples used in test cases were produced by direwolf decoding packets recorded on
WA8LMF's TNC Test CD. http://wa8lmf.net/TNCtest/. Others were modified from this data, created
specifically for use in testing, or decoded from one of the following WebSDRs:
https://websdr3.sdrutah.org
http://dlwis-websdr.ham-radio-op.net:8901/
http://appr.org.br:8901/
"""

from .context import tncexporter
import pytest
import asyncio
import os
import sys
import datetime
import pytest_mock


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
    async def serve_agw_packets(self):
        agw_packets_1 = [
            b'\x00\x00\x00\x00U\x00\x00\x00KF6RAL-6\x00\x00APRS\x00\x00\x00\x00\x00\x00\x8d\x00\x00\x00\x00\x00\x00\x00 1:Fm KF6RAL-6 To APRS Via SHEPRD <UI pid=F0 Len=70 PF=0 >[17:52:54]\r@112331z4044.05N/11212.65W_262/002g005t035r000p002P002h86b10160.DsVP\r\n\r\x00',
            b'\x00\x00\x00\x00U\x00\x00\x00WB7VPC\x00\x00\x00\x00T0TTXX\x00\x00\x00\x00\x7f\x00\x00\x00\x00\x00\x00\x00 1:Fm WB7VPC To T0TTXX Via KF6RAL-1,SHEPRD,WIDE2 <UI pid=F0 Len=42 F=0 >[17:53:16]\r`\'Mpl!n>/]"Cb}146.620MHz ToffON THE ROAD=\r\r\x00',
            b'\x00\x00\x00\x00U\x00\x00\x00HOLDEN\x00\x00\x00\x00APOT30\x00\x00\x00\x00l\x00\x00\x00\x00\x00\x00\x00 1:Fm HOLDEN To APOT30 Via SHEPRD,WIDE2 <UI pid=F0 Len=31 PF=0 >[17:53:57]\r!3901.82N/11209.11W# 12.6V 34F \r\x00',
            b'\x00\x00\x00\x00U\x00\x00\x00KC7YLH-2\x00\x00T0SYPT\x00\x00\x00\x00t\x00\x00\x00\x00\x00\x00\x00 1:Fm KC7YLH-2 To T0SYPT Via SHEPRD,WIDE1,WIDE2-1 <UI pid=F0 Len=29 PF=0 >[17:54:07]\r`\'Vgl Z>/\'"C9}|(2%6\'V|!wwT!|3\r\x00']
        server = AGWServer()
        await AGWServer.establish_connection()
        await AGWServer.send_packets(agw_packets_1)