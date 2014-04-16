#!/usr/bin/env python
# encoding: utf-8
import csv
import logging
import datetime

import geojson
import ogr


log = logging.getLogger(__name__)


class ConversionError(Exception):
    """An error occurred trying to convert a row."""
    pass


class Portland(object):
    """Convert crime data from the City of Portland data to GeoJSON.

    Creates a FeatureCollection of crimes, converting the City's NAD83 coordinates to WGS84.

    The Portland data file CSV column labels (the first row values) are probably:
        "Record ID", "Report Date", "Report Time", "Major Offense Type", "Address",
        "Neighborhood", "Police Precinct", "Police District", "X Coordinate",
        "Y Coordinate"

    The intended public interface of this class is its `to_csv` and `to_geojson` methods, which
    each return the original data restructured into either output format.

    In the case of `to_csv` this can be used with the ``normalize_to_wgs84`` option to the
    constructor to normalize the coordinate data in the original CSV file and retain the same CSV
    format, but with WGS84 coordinates.
    """
    def __init__(self, rows, column_labels=None, normalize_to_wgs84=False):
        if not column_labels:
            self.column_labels = rows.pop(0)

        self._rows = rows
        self.original_row_count = len(self._rows)

        if normalize_to_wgs84:
            self.rows = self.wgs84_rows()
        else:
            self.rows = self._rows

         # State Plane Coordinate System (Oregon North - EPSG:2269, alt: EPSG:2913).
        nad83 = ogr.osr.SpatialReference()
        nad83.ImportFromEPSG(2269)

        # Latitude/longitude (WGS84 - EPSG:4326)
        wgs84 = ogr.osr.SpatialReference()
        wgs84.ImportFromEPSG(4326)

        self.transformation = ogr.osr.CoordinateTransformation(nad83, wgs84)

    def wgs84_rows(self):
        """Normalize all X and Y coordinates to WGS84 (latitude and longitude)

        Replaces ``self.rows`` with a generator that yields a row with WGS84 coordinates.
        """
        for row in self._rows:
            try:
                x, y = self.get_wgs84_point(row)
            except ConversionError:
                continue
            self.set_csv_column(row, 'X Coordinate', x)
            self.set_csv_column(row, 'Y Coordinate', y)
            yield row

    def get_csv_column(self, row, header):
        """A helper to refer to a CSV column index by its name.

        E.g.:
            get(row, 'Record ID')
        """
        return row[self.column_labels.index(header)]

    def set_csv_column(self, row, header, value):
        """A helper to set a CSV column index by its name.

        E.g.:
            set(row, 'Record ID', 1)
        """
        row[self.column_labels.index(header)] = value

    def get_wgs84_point(self, row):
        """Transform coordinates in ``row`` to the WGS84 system.

        Raises ConversionError.
        """
        try:
            x = float(self.get_csv_column(row, 'X Coordinate'))
            y = float(self.get_csv_column(row, 'Y Coordinate'))
        except (ValueError, TypeError):
            log.error('Bad coordinates for row: {}'.format(row))
            raise ConversionError

        coord = self.transformation.TransformPoint(x, y)

        lng = coord[0]
        lat = coord[1]
        return lng, lat

    def parse_date(self, row):
        """Parse a Python datetime object from ``row``.

        Raises ConversionError.
        """
        date_string = '{} {}'.format(self.get_csv_column(row, 'Report Date'),
                                     self.get_csv_column(row, 'Report Time'))

        try:
            date = datetime.datetime.strptime(date_string, '%m/%d/%Y %H:%M:%S')
        except ValueError:
            log.error('Could not parse date for row: {}'.format(row))
            raise ConversionError
        return date

    def to_geojson_feature(self, row):
        """Convert a row of CSV data into a GeoJSON Feature"""
        point = geojson.Point(self.get_wgs84_point(row))
        date = self.parse_date(row)
        feature = geojson.Feature(geometry=point,
                                  id=int(self.get_csv_column(row, 'Record ID')),
                                  properties={
                                      'crimeType': self.get_csv_column(row, 'Major Offense Type'),
                                      'address': self.get_csv_column(row, 'Address'),
                                      'neighborhood': self.get_csv_column(row, 'Neighborhood'),
                                      'policePrecinct': self.get_csv_column(row, 'Police Precinct'),
                                      'policeDistrict': int(self.get_csv_column(row, 'Police District')),
                                      'reportTime': date.isoformat()
                                  })
        return feature

    def to_geojson_feature_collection(self):
        """Convert a list of rows of CSV crime data to GeoJSON FeatureCollection"""
        features = []

        for row in self.rows:
            try:
                features.append(self.to_geojson_feature(row))
            except ConversionError:
                continue

        if not features:
            log.error("No valid Features found in data")

        collection = geojson.FeatureCollection(features)
        return collection

    def to_geojson(self):
        """Convert rows of CSV crime data into a serialized GeoJSON FeatureCollection"""
        collection = self.to_geojson_feature_collection()
        total = len(collection['features'])
        skipped = self.original_row_count - total
        return geojson.dumps(collection, sort_keys=True), total, skipped

    def to_csv(self, file, **csv_options):
        """Convert rows of crime data into a CSV with WGS84 coordinates."""
        total = 0
        writer = csv.writer(file, **csv_options)
        writer.writerow(self.column_labels)
        for row in self.rows:
            writer.writerow(row)
            total += 1
        if total == 0:
            log.error("No valid rows found in file")
        skipped = self.original_row_count - total
        return file, total, skipped
