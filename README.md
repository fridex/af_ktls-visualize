
# Visualizer    [![Badge License]][License]

*For The **[Linux Kernel TLS / DTLS Socket Tool][AF_KTLS Tool]**.*

<br>

## Install

![Badge Fedora]

```sh
dnf install     \
    gnuplot-py  \
    python      \
    numpy       \
    python-{pandas,plumbum,termcolor,jinja2}
```

<br>

## Benchmarks

*You can show benchmarks with:*

```sh
sudo ./client                   \
    --sendfile-mtu 1400         \
    --sendfile-buf file.bin     \
    --drop-caches               \
    --server-host localhost     \
    --server-port 5557          \
    --sendfile file.bin         \
    --payload 1371              \
    --json                      \
    --tls                       \
| ./visualize.py                \
    --html-browse               \
    --html-stats                \
    --output-dir /tmp 
```

*`./client` is from the **AF_TLS** socket tool.*

*See `--help` for more information.*

<br>

## Related

- **[AF_KTLS Tool]**
- **[AF_KTLS]**

<br>


<!---------------------------------------------------------------->

[AF_KTLS Tool]: https://github.com/fridex/af_ktls-tool
[AF_KTLS]: https://github.com/fridex/af_ktls/

[License]: LICENSE


<!---------------------------{ Badges }--------------------------->

[Badge License]: https://img.shields.io/badge/License-GPL_3-blue.svg?style=for-the-badge
[Badge Fedora]: https://img.shields.io/badge/Fedora_23+-51A2DA?style=for-the-badge&logoColor=white&logo=Fedora
