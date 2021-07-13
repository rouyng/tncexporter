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
import asyncio
import pytest
import sys


def setup_env():
    """Setup function for running async subprocesses"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsProactorEventLoopPolicy())


async def run(cmd):
    """asynchronously run a subprocess, useful for running tncexporter in tests"""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if stdout:
        return stdout.decode()
    if stderr:
        return stderr.decode()


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

    # TODO: add integration tests of connection to AGW and KISS interfaces
