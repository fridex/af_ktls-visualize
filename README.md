# Visualization for Linux Kernel TLS/DTLS Socket Tool

This is a simple visualizing tool for [Linux Kernel TLS/DTLS Socket
Tool](https://github.com/fridex/af_ktls-tool)

Installation on Fedora 23 and higher:
```
# dnf install python gnuplot-py numpy python-{pandas,plumbum,termcolor,jinja2}
```
You can visualize benchmarks by (```client``` is from ```AF_TLS``` socket tool):

```
$ sudo ./client --tls --drop-caches --server-host localhost --server-port 5557
--sendfile-buf file.bin --sendfile file.bin --payload 1371 --sendfile-mtu 1400
--json | ./visualize.py --output-dir /tmp --html-stats --html-browse
```

See --help for more info.

See also [AF_KTLS](https://github.com/fridex/af_ktls/), [AF_KTLS
tool](https://github.com/fridex/af_ktls-tool).

