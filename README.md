# TNC exporter
A [prometheus](https://prometheus.io/) exporter for collecting metrics from a [terminal node controller (TNC)](https://en.wikipedia.org/wiki/Terminal_node_controller) used in packet radio networks. These metrics can be visualized in [grafana](https://grafana.com/) using the included dashboard. It utilizes the AGWPE TCP/IP interface, which is implemented by several popular TNC software packages, including [direwolf](https://github.com/wb2osz/direwolf), [UZ7HO sound modem](http://uz7.ho.ua/packetradio.htm) and [AGW Packet Engine](https://www.sv2agw.com/ham#pepro).

## Why should I use it?
TNC exporter provides a powerful interface for collecting and visualizing metrics from your TNC. Using this exporter, prometheus, and grafana, you can visualize at a glance the quantity of packet RX/TX across your TNC, quantity of packets by different type, and distance of packets received (for packets that report location data). You can also customize and build your own visualizations or directly query metrics using prometheus' built-in tools.

Prometheus and Grafana can also be used to monitor a variety of non-TNC-related metrics. As a starting point, I suggest checking out Prometheus' official [node exporter](https://github.com/prometheus/node_exporter). This shows a variety of hardware and OS-level metrics, so if you're running your TNC on e.g. a Raspberry Pi, you can now have a unified dashboard for both system and TNC monitoring.

## What is prometheus and grafana? How do I get started?
[Prometheus](https://prometheus.io/) is a free, open source monitoring tool that allows easy collection and storage of time-series data. Some programs natively export metrics in a prometheus-friendly format, while others require a helper program called an "exporter" that enables prometheus to pull metrics. Prometheus is commonly used to monitor everything from CPU usage to network throughput but has the flexibility to monitor most data that fits in time-series format.

[Grafana](https://grafana.com/) is a popular, open source application for building graphical dashboards that can easily visualize prometheus data in a clear, flexible and beautiful format. TNC exporter includes an example grafana dashboard, but this can be easily modified or replaced to suit your own needs.

*TODO: image of TNC exporter grafana dashboard*

Grafana isn't the only way to visualize prometheus data. You can use prometheus' [built-in expression browser](https://prometheus.io/docs/visualization/browser/), the prometheus templating language to [build your own console](https://prometheus.io/docs/visualization/consoles/), or any third-party tools that support prometheus.

## Metrics exposed by TNC exporter
- packet_rx: Number of packets received (counter)
- packet_tx: Number of packets transmitted (counter)
- packet_distance: Distance of received packets from TNC, for those packet types that report location data (histogram)
- packet_rx_type: Count of packets received by type (counter)

## Installation
In order to visualize TNC metrics using this exporter, there are four steps. First, install prometheus. Then, install the exporter and configure your prometheus instance to pull metrics from it. Next, install grafana. Finally, install the TNC exporter dashboard in grafana and configure it to connect to your prometheus instance.

### System requirements
TNC exporter requires Python 3.9. You can download Python for all major operating systems [here](https://www.python.org/downloads/).

Please consult the [Prometheus](https://prometheus.io/docs/prometheus/latest/getting_started/) and [Grafana documentation](https://grafana.com/docs/grafana/latest/installation/requirements/) for system requirements of those applications.

### Installing prometheus
A full guide on how to install and configure prometheus is outside the scope of this readme. Please consult the [official Prometheus installation guide](https://prometheus.io/docs/prometheus/latest/installation/) or the many other online tutorials available.

### Installing TNC exporter
There are three methods to install TNC exporter
### Install via pip
*TODO: configure PyPI packaging*
### Docker
*TODO: create Dockerfile and add to image registry*
### Manual installation
*TODO: manual installation instructions*

### Installing and configuring grafana
A full guide on how to install and configure grafana is outside the scope of this readme. Please consult the [official Grafana installation guide](https://grafana.com/docs/grafana/latest/installation/) or the many other online tutorials available.

## License
*TODO: create LICENSE.md*