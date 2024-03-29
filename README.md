[![Test and lint](https://github.com/rouyng/tncexporter/actions/workflows/test-lint.yml/badge.svg)](https://github.com/rouyng/tncexporter/actions/workflows/test-lint.yml)
![Python version](https://img.shields.io/github/pipenv/locked/python-version/rouyng/tncexporter)

# TNC exporter

![Screenshot of TNC exporter's Grafana dashboard](grafana-dashboard/dashboard.png)
*Screenshot of TNC exporter's Grafana dashboard, collecting metrics from direwolf decoding the WA8LMF TNC test CD*

A [prometheus](https://prometheus.io/) exporter for collecting metrics from a [terminal node controller (TNC)](https://en.wikipedia.org/wiki/Terminal_node_controller) used in packet radio networks. These metrics can be visualized in [grafana](https://grafana.com/) using the included dashboard. It utilizes the AGW or KISS TCP/IP interfaces provided by the software TNC [direwolf](https://github.com/wb2osz/direwolf). Other TNCs such as [UZ7HO sound modem](http://uz7.ho.ua/packetradio.htm) and [AGW Packet Engine](https://www.sv2agw.com/ham#pepro) that provide AGW or KISS interfaces may also work, but are not officially supported or tested.

- [What does this do? Why should I use it?](#what-does-this-do-why-should-i-use-it)
- [What are prometheus and grafana?](#what-are-prometheus-and-grafana)
- [Metrics](#metrics)
- [Installation guide](#installation-guide)
- [Running and configuring TNC Exporter](#running-and-configuring-tnc-exporter)
- [Support and common issues](#support-and-common-issues)
- [TODO](#todo)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## What does this do? Why should I use it?

TNC exporter uses modern metrics collection and visualization tools (prometheus and grafana) to provide a  legible, beautiful and customizable interface to view and analyze TNC activity over time. This may be particularly useful to packet radio infrastructure operators, such as APRS digipeater/iGate owners who want to better understand usage patterns.

TNC exporter listens on one of the AGW or KISS TCP/IP interfaces provided by your TNC and parses packets decoded and transmitted by the TNC. This packet information is converted into time-series data which can be scraped and stored by a prometheus database and subsequently visualized using a grafana dashboard.

Using this exporter, prometheus, and grafana, you can visualize the following metrics at a glance:
- Quantity of packets received and transmitted by your TNC 
- Quantity of packets by different path and frame type 
- Distance of packets received (for packets that report location data)
- Size of packets

While TNC exporter is packaged with a ready-to-use grafana dashboard to display these metrics, it also allows you to customize how you view your metrics. You can modify the included grafana dashboard, build your own dashboard, or directly query metrics without grafana using prometheus' built-in tools.



## What are prometheus and grafana?
[Prometheus](https://prometheus.io/) is a free, open source monitoring tool that collects and stores time-series data. While prometheus has a built-in web interface, it is primarily designed to collect, store and serve data, not display it. Metrics are collected from various sources by pulling (or "scraping") from HTTP endpoints which host metrics in a prometheus-friendly format. Some programs natively host a prometheus metrics endpoint, while others require a helper program called an "exporter" that collects metrics and creates an endpoint. Administrators, developers and enthusiasts use Prometheus to monitor everything from CPU usage to network throughput. Prometheus has the flexibility to monitor most data that fits in time-series format.

[Grafana](https://grafana.com/) is an open source application for building, viewing and customizing graphical dashboards. Grafana can integrate with a Prometheus server to display time-series data in a variety of legible, customizable and beautiful formats. TNC exporter includes an example grafana dashboard, but this can be easily modified or replaced to suit your own needs.

Grafana isn't the only way to visualize Prometheus time-series data. You can use prometheus' [built-in expression browser](https://prometheus.io/docs/visualization/browser/), the prometheus templating language to [build your own console](https://prometheus.io/docs/visualization/consoles/), or any third-party tools that support Prometheus.

The Prometheus and Grafana combo can also be used to monitor a variety of non-TNC-related metrics. As a starting point, I suggest checking out Prometheus' official [node exporter](https://github.com/prometheus/node_exporter) and [this tutorial](https://grafana.com/oss/prometheus/exporters/node-exporter/) for setting it up. This shows a variety of hardware and OS-level metrics, such as CPU usage, network activity, memory utilization and disk space. This can be very useful to monitor your TNC host machine's status alongside the TNC-specific metrics provided by this exporter.

## Metrics
TNC exporter provides the following metrics. See prometheus docs for a [discussion of the different types of metrics](https://prometheus.io/docs/concepts/metric_types/).

- PACKET_RX: Counter, Number of packets received and decoded. Labeled by path (digipeat or simplex), originating callsign and frame type (U, I,  or S).
- PACKET_TX: Counter, Number of packets transmitted
- MAX_DISTANCE_RECENT: Gauge, Maximum range in meters of position frames received over last time period. Includes digipeated packets.
- MAX_RF_DISTANCE_RECENT: Gauge, Maximum range in meters of non-digipeated position packets received over last time period.
- PACKET_RX_RECENT_PATH: Gauge, number of packets received over last time period. Labels for path type (Simplex/Digipeated).
- PACKET_RX_RECENT_FRAME: Gauge, number of packets received over last time period. Labels for frame type.
- PACKET_TX_RECENT_PATH: Gauge, number of packets transmitted over last time period. Labels for path type.
- RX_PACKET_SIZE: Histogram, size in bytes of received packets. Bucketed in increments of 50 from 0 to 350.
- TX_PACKET_SIZE: Histogram, size in bytes of transmitted packets. Bucketed in increments of 50 from 0 to 350.

*Currently not used in dashboard*
- PACKET_DISTANCE: Summary, Distance in meters of received position packets from TNC (digipeated and RF).
- RF_PACKET_DISTANCE: Summary, Distance in meters of received position packets from TNC (RF only).

## Installation guide
Here is an overview of the steps needed to run TNC exporter, assuming you don't have pre-existing Prometheus and Grafana installations. 
1. Install prometheus. 
2. Install grafana. 
3. Install the TNC exporter dashboard in grafana and configure it to use your prometheus server as a data source.
4. Install TNC exporter and configure your prometheus instance to scrape metrics from the address/port of the exporter.
5. Run direwolf, making sure it is configured to provide a port for an AGW or KISS client
6. Run TNC exporter. To confirm it is connected to your TNC and processing packets, check the exporter's log output on the command line and metrics endpoint.

For detailed instructions, see the subheadings below.

### System requirements
TNC exporter requires Python 3.7 or newer. You can download Python for all major operating systems [here](https://www.python.org/downloads/).

Please consult the [Prometheus](https://prometheus.io/docs/prometheus/latest/getting_started/) and [Grafana documentation](https://grafana.com/docs/grafana/latest/installation/requirements/) for system requirements of those applications.

The total requirements for all these programs are fairly minimal, and all should happily run on a Raspberry Pi 3 or newer, alongside Direwolf. 

### Installing prometheus
A full guide on how to install and configure prometheus is outside the scope of this readme. Please consult the [official Prometheus installation guide](https://prometheus.io/docs/prometheus/latest/installation/) or the many other online tutorials available.

Once prometheus is installed, you will have to [configure it](https://prometheus.io/docs/introduction/first_steps/#configuring-prometheus) to scrape the metrics endpoint created by TNC exporter. 

By default, TNC exporter will expose metrics at port 9110. This should be set as your scrape target within `prometheus.yml` as follows:

```yaml
scrape_configs:
  - job_name: tncexporter
    static_configs:
      - targets: ['localhost:9110']
```

If you have multiple instances of TNC exporter running, you can change the job_name for each instance to something more descriptive.

Once you have prometheus configured and TNC exporter is running, you can check the prometheus web interface to make sure it is scraping metrics from TNC exporter by visiting http://localhost:9090/targets

### Installing grafana
A full guide on how to install and configure grafana is outside the scope of this readme. Please consult the [official Grafana installation guide](https://grafana.com/docs/grafana/latest/installation/) or the many other online tutorials available.

Once you have a working installation of grafana, [import](https://grafana.com/docs/grafana/latest/dashboards/export-import/) the TNC exporter dashboard from the [dashboard json file](grafana-dashboard/tncexporter.json) included in this repository. 

If you are using non-default names for the prometheus data source, or for the TNC exporter scrape job, you may have to adjust each dashboard panel's data source/metrics query accordingly.

### Installing TNC exporter

Download TNC exporter by using the green "Code" download button at the top of this repo page. Alternatively, clone the repository with:

`git clone https://github.com/rouyng/tncexporter.git`

Once you have downloaded a local copy of TNC exporter, open a terminal in the tncexporter directory you just created. At this point I highly recommend creating a python virtual environment before installing dependencies ([see instructions here for using Pipenv or the builtin virtualenv tool](https://docs.python-guide.org/dev/virtualenvs/)). Once you have set up a virtual environment (or not) install the additional required dependencies by running:

`pip3 install -r requirements.txt`

Now you should be ready to [run TNC exporter](#running-and-configuring-tnc-exporter).

## Running and configuring TNC exporter
The basic command to run TNC exporter is:

`python3 -m tncexporter`

There are multiple command line options to configure TNC exporter. See descriptions of these by running:

`python3 -m tncexporter --help` 

### AGW mode vs. KISS mode

By default, TNC exporter tries to connect to an AGW TCP/IP interface at the specified port (default 8000) on a TNC. Alternatively, you can connect to a KISS TCP interface by using the `--kiss-mode` option.

AGW mode is the recommended default because the AGW interface provides "monitoring" functionality that passes both transmitted and received packets to TNC exporter for metrics collection. The KISS interface will only pass received packets, so TNC exporter running in KISS mode will not collect metrics for transmitted packets. 

### Configuring distance metrics
If you want distance metrics, add your TNC's latitude and longitude in decimal degrees as follows:

`python -m tncexporter --latitude 40.7484 --longitude -73.9855`

The above example sets the TNC's position at 40.7484°N, 73.9855°W. South latitudes and west longitudes are entered as negative numbers. TNC exporter will now calculate distances of received position packets relative to this location. 

Please note that TNC exporter does not parse APRS compressed format or Mic-E format position reports. Currently, only packets that provide latitude/longitude in plaintext will update distance metrics. Mic-E/compressed position report parsing is planned for a future release.

### Testing

Once TNC exporter is running and connected to your TNC, you can check that it is publishing metrics by visiting the "/metrics" endpoint with your web browser. By default, this is at: `http://localhost:9110/metrics`

You should see something like the following (actual values may differ if the TNC is actively receiving packets):

```
# HELP tnc_max_range_recent Maximum range in meters of position frames received over last time period. Includes digipeated frames
# TYPE tnc_max_range_recent gauge
tnc_max_range_recent{interval="Last 30 seconds",path="Simplex"} 0
tnc_max_range_recent{interval="Last 30 seconds",path="Digipeated"} 0
# HELP tnc_packet_distance Distance in meters of received position packets from TNC (digipeated and RF)
# TYPE tnc_packet_distance summary
# HELP tnc_packet_rx Number of packets received and decoded
# TYPE tnc_packet_rx counter
# HELP tnc_packet_rx_recent_frame Number of packets received over last time period, labeled by AX.25 frame type
# TYPE tnc_packet_rx_recent_frame gauge
tnc_packet_rx_recent_frame{frame_type="All",interval="Last 30 seconds",path="All"} 0
tnc_packet_rx_recent_frame{frame_type="U",interval="Last 30 seconds",path="All"} 0
tnc_packet_rx_recent_frame{frame_type="I",interval="Last 30 seconds",path="All"} 0
tnc_packet_rx_recent_frame{frame_type="S",interval="Last 30 seconds",path="All"} 0
tnc_packet_rx_recent_frame{frame_type="Unknown",interval="Last 30 seconds",path="All"} 0
# HELP tnc_packet_rx_recent_path Number of packets received over last time period, labeled by path type
# TYPE tnc_packet_rx_recent_path gauge
tnc_packet_rx_recent_path{frame_type="All",interval="Last 30 seconds",path="All"} 0
tnc_packet_rx_recent_path{frame_type="All",interval="Last 30 seconds",path="Simplex"} 0
tnc_packet_rx_recent_path{frame_type="All",interval="Last 30 seconds",path="Digipeated"} 0
# HELP tnc_packet_tx Number of packets transmitted
# TYPE tnc_packet_tx counter
# HELP tnc_packet_tx_recent_path Number of packets transmitted over last time period, labeled by path type
# TYPE tnc_packet_tx_recent_path gauge
tnc_packet_tx_recent_path{frame_type="All",interval="Last 30 seconds",path="All"} 0
tnc_packet_tx_recent_path{frame_type="All",interval="Last 30 seconds",path="Simplex"} 0
tnc_packet_tx_recent_path{frame_type="All",interval="Last 30 seconds",path="Digipeated"} 0
# HELP tnc_rf_packet_distance Distance in meters of received position packets from TNC (RF only)
# TYPE tnc_rf_packet_distance summary
# HELP tnc_rx_packet_size Length in bytes of data field in received packets
# TYPE tnc_rx_packet_size histogram
# HELP tnc_tx_packet_size Length in bytes of data field in transmitted packets
# TYPE tnc_tx_packet_size histogram
```

## Support and common issues

Below are some common questions and issues that you might encounter.

### Q: I'm having trouble setting up prometheus/grafana/direwolf/python, can you help me?
TNC exporter relies on a somewhat complex stack of services to function. You should be prepared to spend a small amount of time familiarizing yourself with all these services for best results. Please do not open issues in this repo for generic prometheus/grafana setup questions, I will close them.

Prometheus and grafana are used in this project because there are huge communities around these services and many tutorials and troubleshooting tips are available online. For these applications, please refer to the prometheus/grafana installation guides linked in the [Installation guide](#installation-guide) above. Many other resources are available via google, youtube and stackoverflow. If you are new to these services, a good tutorial experience is to follow this [node exporter guide](https://grafana.com/oss/prometheus/exporters/node-exporter/). Once you have done this, you are assured of a functioning prometheus/grafana setup and can proceed to configuring TNC exporter. 

If you are having issues setting up direwolf, please refer to that project's excellent [documentation](https://github.com/wb2osz/direwolf/tree/master/doc). In the rare case you have an issue not covered by the documentation, the [direwolf mailing list](https://groups.io/g/direwolf) is very helpful.

If you are having issues installing python, I recommend either [this official installation guide](https://wiki.python.org/moin/BeginnersGuide/Download), or [this more in depth unofficial guide](https://docs.python-guide.org/starting/installation/). Please note that TNC exporter requires Python 3.7. Many issues are caused by having an outdated Python version installed, so please check the installed version first.

### Q: I changed the exporter's update-interval argument and now the plots in some Grafana panels seem wrong. What's going on?
I have tuned the Grafana dashboard panels to match the TNC exporter's default 30 second metrics collection interval. If you adjust this interval by changing the update-interval command line argument, you may need to change some panel settings accordingly. This is only recommended for advanced users who are interested in digging in to the details of Grafana dashboard configuration.

### Q: APRS position packets aren't updating distance metrics, what's up with that?
Make sure you have `--latitude` and `--longitude` command line options set with your desired coordinates when you start TNC exporter.

Please note that TNC exporter does not parse APRS compressed format or Mic-E format position reports. Only those packets that provide latitude/longitude in plaintext update distance metrics. 

 If you're still seeing issues with position packets, please open an [issue](https://github.com/rouyng/tncexporter/issues).

### Q: I am using a TNC other than direwolf and having issues, can you help?
TNC Exporter is designed to use the AGWPE or KISS interfaces that are provided by several TNCs. However, development and testing are primarily done using direwolf. My capacity to provide bugfixes and testing for other TNC software is limited. Users of other TNCS may open an [issue](https://github.com/rouyng/tncexporter/issues) if you have a problem. Developers who wish to improve support for other TNC software are invited to submit pull requests or open an issue to discuss.

### Q: I believe I have found a bug in TNC exporter, where do I report it?
[Open an issue in the github repo](https://github.com/rouyng/tncexporter/issues). It's helpful to include the output of TNC exporter with the `--debug` command line option activated.


## TODO
- Write integration tests
- PyPI packaging
- Test support for other software TNCs such as UZ7HO and AGWPE
- Create Dockerfile
- Parse Mic-E and compressed position report formats to update distance metrics 
- AIS support (via Direwolf, currently have no way to test this as AIS needs a 9600 bps setup)

## Contributing
If you have a bug report or feature request, please open an issue via Github. Code contributions are welcome, please open an issue to propose and discuss changes before submitting substantial pull requests.

## Acknowledgements
This exporter was inspired by claws' excellent [dump1090-exporter](https://github.com/claws/dump1090-exporter/). The design of TNC exporter owes a lot to this project as well as claw's [aioprometheus library](https://github.com/claws/aioprometheus).

Thanks to WB2OSZ and the rest of the [Direwolf software TNC community](https://groups.io/g/direwolf).

Thanks to the ON7LDS website which was the only place I could still find a live copy of the old [AGWPE TCP/IP API Tutorial](https://www.on7lds.net/42/sites/default/files/AGWPEAPI.HTM). This document was an essential reference for this project, so thanks to ON7LDS for archiving it.

## License
Licensed under the terms of the MIT license. See LICENSE.md for more details.
