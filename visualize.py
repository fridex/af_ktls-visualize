#!/bin/env python
#
# Visualization for AF_KTLS socket tool JSON output
#
# Copyright (C) 2016 Fridolin Pokorny <fpokorny@redhat.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.

import os
import sys
import json
import subprocess
import Gnuplot
import numpy
import pandas
import Gnuplot.funcutils
import collections
from datetime import datetime
from plumbum import cli
from termcolor import cprint
from jinja2 import Environment, FileSystemLoader

DEFAULT_OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HTML_STATS_TEMPLATE = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'stats.templ')
INDEX_HTML = 'index.html'


class Visualise(cli.Application):
    VERSION = "0.1a"
    DESCRIPTION = "AF_KTLS visualisation tool for benchmarks"

    output_dir = cli.SwitchAttr(["--output-dir", "-o"], str,
                                help="output directory", default=DEFAULT_OUTPUT_DIR)
    input_file = cli.SwitchAttr(["--input", "-i"], str,
                                help="input JSON file; the default is stdin", default=None)
    html_stats_template = cli.SwitchAttr(["--html-stats-template"], str, requires=["--html-stats"],
                                         help="specify HTML template for HTML output", default=DEFAULT_HTML_STATS_TEMPLATE)

    debug = cli.Flag(["--debug", "-d"],
                     help="show backtrace when an exception occurs")
    nocolor = cli.Flag(["--no-color"],  help="do not use colorized output")
    html_stats = cli.Flag(
        ["--html-stats"], help="output statistics in HTML instead of interactive graphs")
    html_browse = cli.Flag(
        ["--html-browse", "-b"], requires=["--html-stats"], help="browse generated HTML output")

    @staticmethod
    def _test2name(test, escape=False):
        s = "%s (%s)" % (test['test'], test['type'])
        if escape:
            s = s.replace('_', '\\_')
        return s

    @staticmethod
    def plot_prepare(title, xlabels, ylabel, png=None):
        if png:
            gplot = Gnuplot.Gnuplot()
        else:
            gplot = Gnuplot.Gnuplot(persist=1)
        gplot.title(title[0].upper() + title[1:])

        labels_str = []
        for idx, label in enumerate(xlabels):
            labels_str.append('\'%s\' %f' % (label, float(idx) + 0.2))

        gplot('set style histogram')
        gplot('set xtics (%s) rotate by 0' % ",".join(labels_str))
        gplot('set xtics center')
        gplot('set encoding utf8')
        gplot('set border 1|2')
        gplot('set style data histogram')
        gplot('set style fill solid border -1')
        gplot('set boxwidth 1')
        gplot('set yrange [0:]')
        gplot('set key font "Times-New-Roman,13"')
        gplot('set xtics font "Times-New-Roman,13"')
        gplot('set grid ytics noxtics')
        gplot('set key spacing 0')
        gplot('set boxwidth 1')
        gplot('set style fill transparent solid 0.5 noborder')
        gplot('set tic scale 0')

        gplot('set ylabel "%s" font  "Times-New-Roman,16"' % ylabel)
        gplot('set key font "Times-New-Roman,16"')
        gplot('set xtics font "Times-New-Roman,10"')

        if png:
            gplot('set term png')
            gplot('set output "%s"' % png)

        return gplot

    @staticmethod
    def plot_labels_add(plot_data, gplot):
        for idx, val in enumerate(plot_data):
            gplot('set label "%g" at %.3f,%.3f font "Times-New-Roman,10"' %
                  (val, float(idx) + 0.4, float(val) * 5 / 6))
        return gplot

    def make_plots(self, data):
        def plot_ylabel(r):
            if r == 'sent':
                return 'Sent [B]'
            elif r == 'received':
                return 'Received [B]'
            elif r == 'elapsed':
                return 'Elapsed [s]'
            else:
                raise ValueError("Unknown result type")

        def plot_name(r):
            return r[0].upper() + r[1:] + " Statistics"

        def png_name(r):
            if self.html_stats:
                return os.path.join(self.output_dir, "%s.png" % r)
            else:
                return None

        for res_type in ["sent", "received", "elapsed"]:
            name = plot_name(res_type)
            bar_names = [self._test2name(x, escape=True) for x in data]
            ylabel = plot_ylabel(res_type)
            png = png_name(res_type)
            plot_data = [x['result'][res_type] for x in data]

            gplot = self.plot_prepare(name, bar_names, ylabel, png)
            self.plot_labels_add(plot_data, gplot)
            gplot.plot(plot_data)

    def make_html(self, data):
        def get_info():
            res = {
                'uname': ", ".join(os.uname()),
                'generated': str(datetime.now())
            }
            return res

        def make_comparison(data):
            res = []
            for r1 in data:
                line = []
                for r2 in data:
                    if r1 == r2:
                        # avoid floating point errors
                        v = 100
                    elif r2 != 0:
                        v = (r1 * 100) / r2
                    else:
                        v = 0
                    line.append(str(v) + "%")
                res.append(line)
            return res

        names_array = []
        elapsed_array = []
        sent_array = []
        received_array = []
        configuration_array = collections.OrderedDict()

        for idx, test in enumerate(data):
            name = self._test2name(test)
            res = test['result']

            names_array.append(name)
            elapsed_array.append(res['elapsed'])
            sent_array.append(res['sent'])
            received_array.append(res['received'])

            for k, v in test['configuration'].iteritems():
                if k not in configuration_array:
                    configuration_array[k] = len(data) * [" - "]
                configuration_array[k][idx] = v

        sent_df = pandas.DataFrame(numpy.array(
            [[x] for x in sent_array]), index=names_array, columns=['Sent bytes'])
        received_df = pandas.DataFrame(numpy.array(
            [[x] for x in received_array]), index=names_array, columns=['Received bytes'])
        elapsed_df = pandas.DataFrame(numpy.array(
            [[x] for x in elapsed_array]), index=names_array, columns=['Elapsed miliseconds'])
        config_df = pandas.DataFrame(numpy.array(configuration_array.values(
        )), index=configuration_array.keys(), columns=names_array)

        elapsed_cmp_df = pandas.DataFrame(numpy.array(make_comparison(
            elapsed_array)), index=names_array, columns=names_array)
        sent_cmp_df = pandas.DataFrame(numpy.array(make_comparison(
            sent_array)), index=names_array, columns=names_array)
        received_cmp_df = pandas.DataFrame(numpy.array(make_comparison(
            received_array)), index=names_array, columns=names_array)

        template_env = Environment(loader=FileSystemLoader(
            os.path.dirname(self.html_stats_template)))
        template = template_env.get_template(
            os.path.basename(self.html_stats_template))

        html_output = template.render(
            elapsed_stats=elapsed_df.to_html(),
            elapsed_cmp=elapsed_cmp_df.to_html(),
            sent_stats=sent_df.to_html(),
            sent_cmp=sent_cmp_df.to_html(),
            received_stats=received_df.to_html(),
            received_cmp=received_cmp_df.to_html(),
            configurations=config_df.to_html(),
            info=get_info()
        )

        if not os.path.isdir(self.output_dir):
            os.mkdir(self.output_dir)

        with open(os.path.join(self.output_dir, INDEX_HTML), "w") as f:
            f.write(html_output)

    def init(self):
        if not sys.stdout.isatty() or self.nocolor:
            self.print_info = lambda s: sys.stdout.write("INFO: " + str(s))
        else:
            self.print_info = lambda s: cprint("INFO: " + str(s), 'green')

        if not sys.stderr.isatty() or self.nocolor:
            self.print_error = lambda s: sys.stderr.write("ERROR: " + str(s))
            self.print_warn = lambda s: sys.stderr.write("WARN: " + str(s))
        else:
            self.print_error = lambda s: cprint(
                "ERROR: " + str(s), color='red', file=sys.stderr)
            self.print_warn = lambda s: cprint(
                "WARN: " + str(s), color='yellow', file=sys.stderr)

    def parse_input(self):
        if self.input_file is None:
            data = json.load(sys.stdin)
        else:
            with open(self.input_file, 'r') as f:
                data = json.load(f)
        return data

    def main(self):
        self.init()

        try:
            self.print_info("parsing input")
            data = self.parse_input()
            self.print_info("generating plots")
            self.make_plots(data)
            if self.html_stats:
                self.print_info("generating HTML output")
                self.make_html(data)
                if self.html_browse:
                    self.print_info("opening browser")
                    subprocess.call(
                        ('xdg-open', os.path.join(self.output_dir, INDEX_HTML)))
        except Exception as e:
            if self.debug:
                exc_info = sys.exc_info()
                raise exc_info[0], exc_info[1], exc_info[2]
            else:
                self.print_error(str(e))
            return 1

if __name__ == "__main__":
    Visualise.run()
