"""
Unit tests for exporter.py module. Uses pytest framework.

Many packet examples used in test cases were produced by direwolf decoding packets recorded on
WA8LMF's TNC Test CD. http://wa8lmf.net/TNCtest/. Others were modified from this data or created
specifically for use in testing.
"""

from tncexporter import exporter
import pytest


class TestPacketDecodes:
    """
    Unit tests for the exporter.decode_packet function. Tests whether byte strings representing
    raw AGWPE monitor packets are decoded as expected.
    """

    def test_frame_type_ui_1(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KB6CYS\x00\x00\x00\x00BEACON\x00\x00\x00\x00_' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm KB6CYS To BEACON Via N6EX-4 <UI pid=F0 ' \
                     b'Len=24 PF=0 >[14:32:33]\rWEATHER STATION ON-LINE\r\r\x00 '
        test_result = exporter.decode_packet(raw_packet)
        assert test_result['frame_type'] == "U"

    def test_frame_type_ui_2(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KF6WJS-14\x00S4PWYR\x00\x00\x00\x00X\x00\x00' \
                     b'\x00\x00\x00\x00\x00 1:Fm KF6WJS-14 To S4PWYR Via WIDE2-2 <UI pid=F0 ' \
                     b'Len=13 PF=0 >[14:32:38]\r`.a"l!^k/"6b}\r\x00 '
        test_result = exporter.decode_packet(raw_packet)
        assert test_result['frame_type'] == "U"

    def test_frame_type_t(self):
        raw_packet = b'\x00\x00\x00\x00T\x00\x00\x00W6SCE-10\x00\x00APN382\x00\x00\x00\x00\x97' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm W6SCE-10 To APN382 Via WIDE2-1 <UI ' \
                     b'pid=F0 Len=77 PF=0 >[14:33:38]\r!3419.82N111836.06W#PHG6860/W1 on Oat ' \
                     b'Mtn./A=003747/k6ccc@amsat.org for info\r\r\x00 '
        test_result = exporter.decode_packet(raw_packet)
        assert test_result['frame_type'] == "T"

    def test_timestamp_1(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00W6SCE-10\x00\x00APN382\x00\x00\x00\x00\x97' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm W6SCE-10 To APN382 Via WIDE2-1 <UI ' \
                     b'pid=F0 Len=77 PF=0 >[14:33:38]\r!3419.82N111836.06W#PHG6860/W1 on Oat ' \
                     b'Mtn./A=003747/k6ccc@amsat.org for info\r\r\x00 '
        test_result = exporter.decode_packet(raw_packet)
        assert test_result['timestamp'].hour == 14
        assert test_result['timestamp'].minute == 33
        assert test_result['timestamp'].second == 38

    def test_timestamp_2(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00W6SCE-10\x00\x00APN382\x00\x00\x00\x00\x97' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm W6SCE-10 To APN382 Via WIDE2-1 <UI ' \
                     b'pid=F0 Len=77 PF=0 >[00:11:56]\r!3419.82N111836.06W#PHG6860/W1 on Oat ' \
                     b'Mtn./A=003747/k6ccc@amsat.org for info\r\r\x00 '
        test_result = exporter.decode_packet(raw_packet)
        assert test_result['timestamp'].hour == 0
        assert test_result['timestamp'].minute == 11
        assert test_result['timestamp'].second == 56



