"""
Unit tests for exporter.py module. Uses pytest framework.

Many packet examples used in test cases were produced by direwolf decoding packets recorded on
WA8LMF's TNC Test CD. http://wa8lmf.net/TNCtest/. Others were modified from this data, created
specifically for use in testing, or decoded from one of the following WebSDRs:
https://websdr3.sdrutah.org
http://dlwis-websdr.ham-radio-op.net:8901/
http://appr.org.br:8901/
"""

from tncexporter import exporter
import pytest


class TestPacketParsing:
    """
    Unit tests for the exporter.decode_packet function. Tests whether byte strings representing
    raw AGWPE monitor packets are decoded as expected.
    """
    # Test that frame type is properly parsed from packet header
    def test_frame_type_ui_1(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KB6CYS\x00\x00\x00\x00BEACON\x00\x00\x00\x00_' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm KB6CYS To BEACON Via N6EX-4 <UI pid=F0 ' \
                     b'Len=24 PF=0 >[14:32:33]\rWEATHER STATION ON-LINE\r\r\x00 '
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['frame_type'] == "U"

    def test_frame_type_ui_2(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KF6WJS-14\x00S4PWYR\x00\x00\x00\x00X\x00\x00' \
                     b'\x00\x00\x00\x00\x00 1:Fm KF6WJS-14 To S4PWYR Via WIDE2-2 <UI pid=F0 ' \
                     b'Len=13 PF=0 >[14:32:38]\r`.a"l!^k/"6b}\r\x00 '
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['frame_type'] == "U"

    def test_frame_type_t(self):
        raw_packet = b'\x00\x00\x00\x00T\x00\x00\x00W6SCE-10\x00\x00APN382\x00\x00\x00\x00\x97' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm W6SCE-10 To APN382 Via WIDE2-1 <UI ' \
                     b'pid=F0 Len=77 PF=0 >[14:33:38]\r!3419.82N111836.06W#PHG6860/W1 on Oat ' \
                     b'Mtn./A=003747/k6ccc@amsat.org for info\r\r\x00 '
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['frame_type'] == "T"

    # Test that timestamps are parsed from frame header
    def test_timestamp_1(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00W6SCE-10\x00\x00APN382\x00\x00\x00\x00\x97' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm W6SCE-10 To APN382 Via WIDE2-1 <UI ' \
                     b'pid=F0 Len=77 PF=0 >[14:33:38]\r!3419.82N111836.06W#PHG6860/W1 on Oat ' \
                     b'Mtn./A=003747/k6ccc@amsat.org for info\r\r\x00 '
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['timestamp'].hour == 14
        assert test_result['timestamp'].minute == 33
        assert test_result['timestamp'].second == 38

    def test_timestamp_2(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00W6SCE-10\x00\x00APN382\x00\x00\x00\x00\x97' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm W6SCE-10 To APN382 Via WIDE2-1 <UI ' \
                     b'pid=F0 Len=77 PF=0 >[00:11:56]\r!3419.82N111836.06W#PHG6860/W1 on Oat ' \
                     b'Mtn./A=003747/k6ccc@amsat.org for info\r\r\x00 '
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['timestamp'].hour == 0
        assert test_result['timestamp'].minute == 11
        assert test_result['timestamp'].second == 56

    def test_timestamp_3(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00AG7LY-7\x00\x00\x00TQQYRR\x00\x00\x00\x00f' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm AG7LY-7 To TQQYRR Via SHEPRD,WIDE1,' \
                     b'WIDE2-1 <UI pid=F0 Len=17 F=0 >[17:54:31]\r`(Y[rIY[/`"BL}_(\r\r\x00'
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 54
        assert test_result['timestamp'].second == 31

    def test_timestamp_4(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KC7ZNH-2\x00\x00T0SVTS\x00\x00\x00\x00z\x00' \
                     b'\x00\x00\x00\x00\x00\x00 1:Fm KC7ZNH-2 To T0SVTS Via SHEPRD,WIDE1,' \
                     b'WIDE2-1 <UI pid=F0 Len=35 PF=0 >[17:58:50]\r`\'U=l F>/\'"Bg}MT-RTG|*[' \
                     b'%9\'N|!wt#!|3\r\x00'
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 58
        assert test_result['timestamp'].second == 50

    # test that latitude/longitude is parsed from position frames
    def test_latlon_1(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KJ7BC-9\x00\x00\x00APTT4\x00\x00\x00\x00\x00' \
                     b'\x96\x00\x00\x00\x00\x00\x00\x00 1:Fm KJ7BC-9 To APTT4 Via SHEPRD,WIDE1,' \
                     b'WIDE2-2 <UI pid=F0 Len=65 PF=0 >[' \
                     b'17:56:25]\r/005623h4037.97N/11159.06Wv024/000/TT4Alpha.68 on ' \
                     b'Safari/A=004561\r\x00'
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['lat_lon'] == (4037.97, -11159.06)

    def test_latlon_2(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00BLOW\x00\x00\x00\x00\x00\x00APDW14\x00\x00' \
                     b'\x00\x00\x7f\x00\x00\x00\x00\x00\x00\x00 1:Fm BLOW To APDW14 Via RCHFLD,' \
                     b'SHEPRD,WIDE2 <UI pid=F0 Len=45 PF=0 >[' \
                     b'17:57:56]\r!3735.51NS11251.96W#PHG3140BLOWHARD MT, AL7BX\r\x00'
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['lat_lon'] == (3735.51, -11251.96)

    def test_latlon_3(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00W6SCE-10\x00\x00APN382\x00\x00\x00\x00\x97' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm W6SCE-10 To APN382 Via WIDE2-1 <UI ' \
                     b'pid=F0 Len=77 PF=0 >[14:33:38]\r!3419.82N111836.06W#PHG6860/W1 on Oat ' \
                     b'Mtn./A=003747/k6ccc@amsat.org for info\r\r\x00 '
        test_result = exporter.parse_packet(raw_packet)
        assert test_result['lat_lon'] == (3419.82, -11836.06)

class TestHaversine:
    """Test distance calculations performed by exporter.haversine_distance()"""

    def test_haversine_1(self):
        point1 = (-2.74, -44.14)
        point2 = (42.32, -113.04)
        distance = exporter.haversine_distance(point1, point2)
        assert round(distance, 2) == 8504802.16

    def test_haversine_2(self):
        point1 = (33.32, -111.94)
        point2 = (33.42, -111.60)
        distance = exporter.haversine_distance(point1, point2)
        assert round(distance, 2) == 33474.17
