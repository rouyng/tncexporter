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


# TODO: integration tests