#!/usr/bin/env python
# encoding: utf-8
import argparse
import csv
import os

from crimetools.converters.portland import Portland


class Command(object):
    def __init__(self, opts):
        self.options = opts

        with open(opts.in_filename, 'r') as f:
            self.rows = [row for row in csv.reader(f)]

        # This script only handles Portland data for now
        if opts.location == 'portland':
            self.converter = Portland(self.rows, normalize_to_wgs84=self.options.use_wgs84)
        else:
            raise ValueError("No location handler for {}".format(opts.location))

    def report_empty_result(self):
        """Report that no results were converted from the input file."""
        print('Could not find any valid data in the file.')
        skipped = len(self.rows)
        total = 0
        return total, skipped

    def convert_json(self):
        result, total, skipped = self.converter.to_geojson()

        if not result:
            return self.report_empty_result()

        with open(self.options.out_filename, 'w') as out_file:
            out_file.write(result)
            return total, skipped

    def convert_csv(self):
        is_new_file = os.path.exists(self.options.out_filename)

        with open(self.options.out_filename, 'w', encoding='UTF8', newline='') as out_file:
            result, total, skipped = self.converter.to_csv(out_file)

            if not total:
                out_file.close()
                if is_new_file:
                    os.unlink(out_file.name)
                return self.report_empty_result()

            return total, skipped

    def run(self):
        """Convert a CSV file of crime data from ``in_filename`` to a file in ``out_format`` named
        ``out_filename``.

        Returns the number of rows skipped.
        """
        if self.options.format == 'geojson':
            total, skipped = self.convert_json()
        elif self.options.format == 'csv':
            total, skipped = self.convert_csv()
        else:
            "Format not supported: {}".format(self.options.format)
            return

        print('\t{} records converted'.format(total))

        if skipped:
            print('\t{} records skipped due to bad data'.format(skipped))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', action='store', dest='in_filename', required=True, help='The path to the file to read data from')
    parser.add_argument('-o', action='store', dest='out_filename', required=True, help='The path to the file to write data to')
    parser.add_argument('-l', action='store', choices=['portland'], dest='location', required=True, help='The location converter to use')
    parser.add_argument('-f', action='store', choices=['csv', 'geojson'], dest='format', required=True, help='The format to use for output data')
    parser.add_argument('--wgs84', action='store_true', dest='use_wgs84', help='Normalize to WGS84 coordinates')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')

    options = parser.parse_args()

    command = Command(options)
    command.run()
