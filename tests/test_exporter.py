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


class TestPacketParsing:
    """
    Unit tests for the exporter.decode_packet function. Tests whether byte strings representing
    raw AGWPE monitor packets are decoded as expected.
    """

    # TODO: add unit tests for parse_packet_kiss method

    def test_parse_1(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KB6CYS\x00\x00\x00\x00BEACON\x00\x00\x00\x00_' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm KB6CYS To BEACON Via N6EX-4 <UI pid=F0 ' \
                     b'Len=24 PF=0 >[14:32:33]\rWEATHER STATION ON-LINE\r\r\x00 '
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'KB6CYS'
        assert test_result['call_to'] == 'BEACON'
        assert test_result['timestamp'].hour == 14
        assert test_result['timestamp'].minute == 32
        assert test_result['timestamp'].second == 33
        assert test_result['hops_count'] == 1
        assert test_result['hops_path'] == ['N6EX-4']
        assert test_result['lat_lon'] == (None, None)

    def test_parse_2(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KF6WJS-14\x00S4PWYR\x00\x00\x00\x00X\x00\x00' \
                     b'\x00\x00\x00\x00\x00 1:Fm KF6WJS-14 To S4PWYR Via WIDE2-2 <UI pid=F0 ' \
                     b'Len=13 PF=0 >[14:32:38]\r`.a"l!^k/"6b}\r\x00 '
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'KF6WJS-14'
        assert test_result['call_to'] == 'S4PWYR'
        assert test_result['timestamp'].hour == 14
        assert test_result['timestamp'].minute == 32
        assert test_result['timestamp'].second == 38
        assert test_result['hops_count'] == 0
        assert test_result['hops_path'] == []
        assert test_result['lat_lon'] == (None, None)

    def test_parse_3(self):
        raw_packet = b'\x00\x00\x00\x00T\x00\x00\x00W6SCE-10\x00\x00APN382\x00\x00\x00\x00\x97' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm W6SCE-10 To APN382 Via WIDE2-1 <UI ' \
                     b'pid=F0 Len=77 PF=0 >[14:33:38]\r!3419.82N111836.06W#PHG6860/W1 on Oat ' \
                     b'Mtn./A=003747/k6ccc@amsat.org for info\r\r\x00 '
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "T"
        assert test_result['call_from'] == 'W6SCE-10'
        assert test_result['call_to'] == 'APN382'
        assert test_result['timestamp'].hour == 14
        assert test_result['timestamp'].minute == 33
        assert test_result['timestamp'].second == 38
        assert test_result['hops_count'] == 0
        assert test_result['hops_path'] == []
        assert test_result['lat_lon'] == (34.1982, -118.3606)

    def test_parse_4(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00AG7LY-7\x00\x00\x00TQQYRR\x00\x00\x00\x00f' \
                     b'\x00\x00\x00\x00\x00\x00\x00 1:Fm AG7LY-7 To TQQYRR Via SHEPRD,WIDE1,' \
                     b'WIDE2-1 <UI pid=F0 Len=17 F=0 >[17:54:31]\r`(Y[rIY[/`"BL}_(\r\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'AG7LY-7'
        assert test_result['call_to'] == 'TQQYRR'
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 54
        assert test_result['timestamp'].second == 31
        assert test_result['hops_count'] == 1
        assert test_result['hops_path'] == ['SHEPRD']
        assert test_result['lat_lon'] == (None, None)

    def test_parse_5(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KC7ZNH-2\x00\x00T0SVTS\x00\x00\x00\x00z\x00' \
                     b'\x00\x00\x00\x00\x00\x00 1:Fm KC7ZNH-2 To T0SVTS Via SHEPRD,WIDE1,' \
                     b'WIDE2-1 <UI pid=F0 Len=35 PF=0 >[17:58:50]\r`\'U=l F>/\'"Bg}MT-RTG|*[' \
                     b'%9\'N|!wt#!|3\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'KC7ZNH-2'
        assert test_result['call_to'] == 'T0SVTS'
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 58
        assert test_result['timestamp'].second == 50
        assert test_result['hops_count'] == 1
        assert test_result['hops_path'] == ['SHEPRD']
        assert test_result['lat_lon'] == (None, None)

    def test_parse_6(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00KJ7BC-9\x00\x00\x00APTT4\x00\x00\x00\x00\x00' \
                     b'\x96\x00\x00\x00\x00\x00\x00\x00 1:Fm KJ7BC-9 To APTT4 Via SHEPRD,WIDE1,' \
                     b'WIDE2-2 <UI pid=F0 Len=65 PF=0 >[' \
                     b'17:56:25]\r/005623h4037.97N/11159.06Wv024/000/TT4Alpha.68 on ' \
                     b'Safari/A=004561\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'KJ7BC-9'
        assert test_result['call_to'] == 'APTT4'
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 56
        assert test_result['timestamp'].second == 25
        assert test_result['hops_count'] == 1
        assert test_result['hops_path'] == ['SHEPRD']
        assert test_result['lat_lon'] == (40.3797, -111.5906)

    def test_parse_7(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00BLOW\x00\x00\x00\x00\x00\x00APDW14\x00\x00' \
                     b'\x00\x00\x7f\x00\x00\x00\x00\x00\x00\x00 1:Fm BLOW To APDW14 Via RCHFLD,' \
                     b'SHEPRD,WIDE2 <UI pid=F0 Len=45 PF=0 >[' \
                     b'17:57:56]\r!3735.51NS11251.96W#PHG3140BLOWHARD MT, AL7BX\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'BLOW'
        assert test_result['call_to'] == 'APDW14'
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 57
        assert test_result['timestamp'].second == 56
        assert test_result['hops_count'] == 2
        assert test_result['hops_path'] == ['RCHFLD', 'SHEPRD']
        assert test_result['lat_lon'] == (37.3551, -112.5196)

    def test_parse_8(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00DO0HWI\x00\x00\x00\x00APMI04\x00\x00\x00\x00' \
                     b'\x8b\x00\x00\x00\x00\x00\x00\x00 1:Fm DO0HWI To APMI04 Via DB0KUE <UI ' \
                     b'pid=F0 Len=68 PF=0 >[16:27:50]\r@192327z5354.08N/01124.80E#APRS Digipeater ' \
                     b'& IGate in Wismar, OV V13\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'DO0HWI'
        assert test_result['call_to'] == 'APMI04'
        assert test_result['timestamp'].hour == 16
        assert test_result['timestamp'].minute == 27
        assert test_result['timestamp'].second == 50
        assert test_result['hops_count'] == 1
        assert test_result['hops_path'] == ['DB0KUE']
        assert test_result['lat_lon'] == (53.5408, 11.2480)

    def test_parse_9(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00DB0HRO\x00\x00\x00\x00APZ18\x00\x00\x00\x00' \
                     b'\x00\x89\x00\x00\x00\x00\x00\x00\x00 1:Fm DB0HRO To APZ18 Via WIDE2 <UI ' \
                     b'pid=F0 Len=69 P=0 >[16:26:40]\rtxt ;DB0HRO/FM*272108z5408.37N/01202.82EmFM ' \
                     b'Relais DB0HRO 145,775 MHz\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'DB0HRO'
        assert test_result['call_to'] == 'APZ18'
        assert test_result['timestamp'].hour == 16
        assert test_result['timestamp'].minute == 26
        assert test_result['timestamp'].second == 40
        assert test_result['hops_count'] == 0
        assert test_result['hops_path'] == []
        assert test_result['lat_lon'] == (54.0837, 12.0282)

    def test_parse_10(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00PU2WZA-15\x00APN383\x00\x00\x00\x00q\x00\x00' \
                     b'\x00\x00\x00\x00\x00 1:Fm PU2WZA-15 To APN383 <UI pid=F0 Len=50 PF=0 >[' \
                     b'17:05:23]\r!2254.81S/04826.34W# Aprs - Botucatu SP bY PU2PHF\r\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'PU2WZA-15'
        assert test_result['call_to'] == 'APN383'
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 5
        assert test_result['timestamp'].second == 23
        assert test_result['hops_count'] == 0
        assert test_result['hops_path'] == []
        assert test_result['lat_lon'] == (-22.5481, -48.2634)

    def test_parse_11(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00PY2KCA-15\x00APMI01\x00\x00\x00\x00~\x00\x00' \
                     b'\x00\x00\x00\x00\x00 1:Fm PY2KCA-15 To APMI01 Via PU2LYJ-15 <UI pid=F0 ' \
                     b'Len=49 PF=0 >[17:00:52]\r@200000z2234.97S/04710.61W#GRUPO PAULISTA DE ' \
                     b'APRS\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'PY2KCA-15'
        assert test_result['call_to'] == 'APMI01'
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 0
        assert test_result['timestamp'].second == 52
        assert test_result['hops_count'] == 1
        assert test_result['hops_path'] == ['PU2LYJ-15']
        assert test_result['lat_lon'] == (-22.3497, -47.1061)

    def test_parse_12(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00BX2ADJ-2\x00\x00APAVT7\x00\x00\x00\x00^\x00' \
                     b'\x00\x00\x00\x00\x00\x00 1:Fm BX2ADJ-2 To APAVT7 Via WIDE1-1 <UI pid=F0 ' \
                     b'Len=20 PF=0 >[17:27:43]\r!2500.63N/12128.06Er\r\x00 '
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'BX2ADJ-2'
        assert test_result['call_to'] == 'APAVT7'
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 27
        assert test_result['timestamp'].second == 43
        assert test_result['hops_count'] == 0
        assert test_result['hops_path'] == []
        assert test_result['lat_lon'] == (25.0063, 121.2806)

    def test_parse_13(self):
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00BM2MCF-12\x00APAVTT\x00\x00\x00\x00\x8a\x00' \
                     b'\x00\x00\x00\x00\x00\x00 1:Fm BM2MCF-12 To APAVTT Via BX2ADJ-2,WIDE1,' \
                     b'WIDE2-1 <UI pid=F0 Len=48 PF=0 >[17:44:31]\r!2459.75N/12123.05ErPHG2760 ' \
                     b'DIGI_144.640M 05.40V\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'BM2MCF-12'
        assert test_result['call_to'] == 'APAVTT'
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 44
        assert test_result['timestamp'].second == 31
        assert test_result['hops_count'] == 1
        assert test_result['hops_path'] == ['BX2ADJ-2']
        assert test_result['lat_lon'] == (24.5975, 121.2305)

    def test_parse_14(self):
        """This test checks parsing of uncommon comma separated lat/lon values"""
        raw_packet = b'\x00\x00\x00\x00U\x00\x00\x00BM2MCF-12\x00APAVTT\x00\x00\x00\x00\x8a\x00' \
                     b'\x00\x00\x00\x00\x00\x00 1:Fm BM2MCF-12 To APAVTT Via BX2ADJ-2,WIDE1,' \
                     b'WIDE2-1 <UI pid=F0 Len=48 PF=0 >[17:44:31]\r$GPGGA,021511.000,4847.8301,N,' \
                     b'00829.8295,E,2,11,0.9,714.1,M,47.9,M,1.8,0000*7EF0 Len=79 PF=0 >' \
                     b'[19:15:16]\r\x00'
        test_result = tncexporter.exporter.TNCExporter.parse_packet_agw(raw_packet)
        assert test_result['frame_type'] == "U"
        assert test_result['call_from'] == 'BM2MCF-12'
        assert test_result['call_to'] == 'APAVTT'
        assert test_result['timestamp'].hour == 17
        assert test_result['timestamp'].minute == 44
        assert test_result['timestamp'].second == 31
        assert test_result['hops_count'] == 1
        assert test_result['hops_path'] == ['BX2ADJ-2']
        assert test_result['lat_lon'] == (48.4783, 8.2982)


class TestHaversine:
    """Test distance calculations performed by exporter.haversine_distance()"""

    def test_haversine_1(self):
        point1 = (-2.74, -44.14)
        point2 = (42.32, -113.04)
        distance = tncexporter.exporter.TNCExporter.haversine_distance(point1, point2)
        assert round(distance, 2) == 8504802.16

    def test_haversine_2(self):
        point1 = (33.32, -111.94)
        point2 = (33.42, -111.60)
        distance = tncexporter.exporter.TNCExporter.haversine_distance(point1, point2)
        assert round(distance, 2) == 33474.17
