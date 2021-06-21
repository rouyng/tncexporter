# TNC exporter
A [prometheus](https://prometheus.io/) exporter for collecting metrics from a [terminal node controller (TNC)](https://en.wikipedia.org/wiki/Terminal_node_controller) used in packet radio networks. These metrics can be visualized in [grafana](https://grafana.com/) using the included dashboard. It utilizes the AGWPE TCP/IP interface, which is implemented by several popular TNC software packages, including [direwolf](https://github.com/wb2osz/direwolf), [UZ7HO sound modem](http://uz7.ho.ua/packetradio.htm) and [AGW Packet Engine](https://www.sv2agw.com/ham#pepro).

- [Why should I use it?](#Why should I use it?)
- What are prometheus and grafana?
- Installation guide
- Customization
- Support and common issues
- TODO
- Contributing
- License

## Why should I use it?
TNC exporter provides a powerful interface for collecting and visualizing metrics from your TNC. Using this exporter, prometheus, and grafana, you can visualize at a glance the quantity of packet RX/TX across your TNC, quantity of packets by different path and frame type, and distance of packets received (for packets that report location data). You can also customize the example grafana dashboard, build your own or directly query metrics using prometheus' built-in tools. 

## What are prometheus and grafana?
[Prometheus](https://prometheus.io/) is a free, open source monitoring tool that collects and stores time-series data. While prometheus has a build-in web interface, it is primarily designed to store and serve data, not display it. Some programs natively export metrics in a prometheus-friendly format, while others require a helper program called an "exporter" that enables prometheus to pull metrics. Administrators, developers and enthusiasts use Prometheus to monitor everything from CPU usage to network throughput. Prometheus has the flexibility to monitor most data that fits in time-series format.

[Grafana](https://grafana.com/) is an open source application for building, viewing and customizing graphical dashboards. Grafana can integrate with a Prometheus server to display time-series data in a variety of legible, flexible and beautiful formats. TNC exporter includes an example grafana dashboard, but this can be easily modified or replaced to suit your own needs.

*TODO: image of TNC exporter grafana dashboard*

Grafana isn't the only way to visualize Prometheus time-series data. You can use prometheus' [built-in expression browser](https://prometheus.io/docs/visualization/browser/), the prometheus templating language to [build your own console](https://prometheus.io/docs/visualization/consoles/), or any third-party tools that support pPrometheus.

The Prometheus and Grafana combo can also be used to monitor a variety of non-TNC-related metrics. As a starting point, I suggest checking out Prometheus' official [node exporter](https://github.com/prometheus/node_exporter). This shows a variety of hardware and OS-level metrics, such as CPU usage, network activity, memory utilization and disk space. This can be very useful to monitor your TNC host machine's status alongside the TNC-specific metrics provided by this exporter.

## Metrics exposed by TNC exporter
- packet_rx: Number of packets received and decoded (counter)
- packet_tx: Number of packets transmitted (counter)
- packet_distance: Distance of received packets from TNC, for those packet types that report location data (histogram)
- packet_rx_type: Count of packets received by type (counter)
- packet_rx_callsign: Count of packets received by callsign (histogram)

## Installation guide
In order to visualize TNC metrics using this exporter, there are four steps:
1. Install prometheus. 
2. Install the exporter and configure your prometheus instance to pull metrics from it.  
3. Install grafana. 
4. Install the TNC exporter dashboard in grafana and configure it to use your prometheus server as a data source.
5. Run direwolf, making sure it is configured to expose an 


### System requirements
TNC exporter requires Python 3.9. You can download Python for all major operating systems [here](https://www.python.org/downloads/).

Please consult the [Prometheus](https://prometheus.io/docs/prometheus/latest/getting_started/) and [Grafana documentation](https://grafana.com/docs/grafana/latest/installation/requirements/) for system requirements of those applications.

### Installing prometheus
A full guide on how to install and configure prometheus is outside the scope of this readme. Please consult the [official Prometheus installation guide](https://prometheus.io/docs/prometheus/latest/installation/) or the many other online tutorials available.

### Installing TNC exporter

*TODO: manual installation instructions*

#### Running TNC exporter
The basic command to invoke tncexporter is:

`python -m tncexporter`

There are multiple command line options to configure tncexporter. See descriptions of these by running:

`python -m tncexporter --help` 


### Installing and configuring grafana
A full guide on how to install and configure grafana is outside the scope of this readme. Please consult the [official Grafana installation guide](https://grafana.com/docs/grafana/latest/installation/) or the many other online tutorials available.

Once you have a working installation of grafana, [import](https://grafana.com/docs/grafana/latest/dashboards/export-import/) the tncexporter dashboard from the [dashboard json file](grafana-dashboard/tncexporter.json) included in this repository.



## Support and common issues

Below are some common questions and issues that you might encounter.

### Q: I'm having trouble setting up prometheus/grafana/direwolf/python, can you help me?
tncexporter relies on a somewhat complex stack of services to function. You should be prepared to spend a small amount of time familiarizing yourself with all these services for best results. As a single, unpaid open source developer I have limited capacity to personally provide support for all components of this stack. Please do not open issues in this repo for generic prometheus/grafana setup questions, I will close them.

Prometheus and grafana are used in this project because there are huge communities around these services and many tutorials and troubleshooting tips are available online. For these applications, please refer to the prometheus/grafana installation guides linked in the "Installation" section below. Many other resources are available via google, youtube and stackoverflow. If you are new to these services, a good tutorial experience is to setup [node exporter](https://github.com/prometheus/node_exporter) and the associated grafana dashboard. Once you have done this, you are assured of a functioning basic setup and can proceed to configuring tncexporter. 

If you are having issues setting up direwolf, please refer to that project's excellent [documentation](https://github.com/wb2osz/direwolf/tree/master/doc). In the rare case you have an issue not covered by the documentation, the [Direwolf mailing list](https://groups.io/g/direwolf) is very helpful.

### Q: I changed the exporter's update-interval argument and now the metrics seem off
Please note that I have tuned the dashboard panels to match the tncexporter's default 30 second metrics collection interval. If you adjust this interval by changing the update-interval command line argument, you may need to change some panel settings accordingly. 




## TODO
- PyPI packaging
- Create Dockerfile
- Test support for other software TNCs such as UZ7HO and AGWPE
- AIS support (via Direwolf, currently have no way to test this as AIS needs a 9600 bps setup)

## Contributing
If you have a bug report or feature request, please open an issue via Github. Code contributions are welcome, please open an issue to propose and discuss changes before submitting substantial pull requests.

## Acknowledgements
This exporter was inspired by claws' excellent [dump1090-exporter](https://github.com/claws/dump1090-exporter/). The design of tncexporter owes a lot to this project as well as claw's [aioprometheus library](https://github.com/claws/aioprometheus).

Thanks to WB2OSZ and the rest of the [Direwolf software TNC community](https://groups.io/g/direwolf).

Thanks to the ON7LDS website which was the only place I could still find a live copy of the old [AGWPE TCP/IP API Tutorial](https://www.on7lds.net/42/sites/default/files/AGWPEAPI.HTM). This document was an essential reference for this project, so thanks to ON7LDS for archiving it.

## License
Licensed under the terms of the MIT license. See LICENSE.md for more details.