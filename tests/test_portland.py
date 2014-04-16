#!/usr/bin/env python
# encoding: utf-8
import csv
import io
import os
import geojson
import tempfile
import unittest
import sys

import crimetools.converters


COLUMN_LABELS = [
    "Record ID", "Report Date", "Report Time", "Major Offense Type", "Address",
    "Neighborhood", "Police Precinct", "Police District", "X Coordinate",
    "Y Coordinate"
]


class TestPortlandToGeojson(unittest.TestCase):
    def test_converts_row_to_feature(self):
        """The Converter should convert good data into a Feature"""
        csvRow = ["13807517", "12/01/2011", "01:00:00", "Liquor Laws",
                  "NE WEIDLER ST and NE 1ST AVE PORTLAND, OR 97232", "LLOYD", "PORTLAND PREC NO",
                  "690", 7647471.0160800004, 688344.45013000001]

        expected = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [-122.66469510763777, 45.53435699129174],
                        "type": "Point"
                    },
                    "id": 13807517,
                    "properties": {
                        'crimeType': 'Liquor Laws',
                        'address': 'NE WEIDLER ST and NE 1ST AVE PORTLAND, OR 97232',
                        'neighborhood': 'LLOYD',
                        'policePrecinct': 'PORTLAND PREC NO',
                        'policeDistrict': 690,
                        'reportTime': "2011-12-01T01:00:00"
                    },
                    "type": "Feature"
                }
            ],
            "type": "FeatureCollection"
        }

        converter = crimetools.converters.Portland([COLUMN_LABELS, csvRow])
        actual, _, _ = converter.to_geojson()

        self.assertEqual(geojson.dumps(expected, sort_keys=True), actual)

    def test_bad_float_x(self):
        """The Converter should skip a row if "X Coordinate" is not floaty"""
        csvRow = ["13807517", "12/01/2011", "01:00:00", "Liquor Laws",
                  "NE WEIDLER ST and NE 1ST AVE PORTLAND, OR 97232", "LLOYD", "PORTLAND PREC NO",
                  "690", "Bad X Coordinate", 688344.45013000001]
        converter = crimetools.converters.Portland([COLUMN_LABELS, csvRow], normalize_to_wgs84=True)
        result, total, skipped = converter.to_geojson()
        result = geojson.loads(result)

        expected_skipped = 1
        self.assertEqual(expected_skipped, skipped)

        expected_length = 0
        self.assertEqual(expected_length, len(result['features']))

    def test_bad_float_y(self):
        """The Converter should skip a row if "Y Coordinate" is not floaty"""
        csvRow = ["13807517", "12/01/2011", "01:00:00", "Liquor Laws",
                  "NE WEIDLER ST and NE 1ST AVE PORTLAND, OR 97232", "LLOYD", "PORTLAND PREC NO",
                  "690", 7647471.0160800004, "Bad Y Coordinate"]
        converter = crimetools.converters.Portland([COLUMN_LABELS, csvRow])
        result, total, skipped = converter.to_geojson()
        result = geojson.loads(result)

        expected_skipped = 1
        self.assertEqual(expected_skipped, skipped)

        expected_length = 0
        self.assertEqual(expected_length, len(result['features']))

    def test_bad_date(self):
        """The Converter should skip a row if "Report Date" is not parsable into a date"""
        csvRow = ["13807517", "Bad Date", "01:00:00", "Liquor Laws",
                  "NE WEIDLER ST and NE 1ST AVE PORTLAND, OR 97232", "LLOYD", "PORTLAND PREC NO",
                  "690", 7647471.0160800004, 688344.45013000001]
        converter = crimetools.converters.Portland([COLUMN_LABELS, csvRow])
        result, total, skipped = converter.to_geojson()
        result = geojson.loads(result)

        expected_skipped = 1
        self.assertEqual(expected_skipped, skipped)

        expected_length = 0
        self.assertEqual(expected_length, len(result['features']))

    def test_bad_time(self):
        """The Converter should skip a row if "Report Time" is not parsable"""
        csvRow = ["13807517", "12/01/2011", "Bad Time", "Liquor Laws",
                  "NE WEIDLER ST and NE 1ST AVE PORTLAND, OR 97232", "LLOYD", "PORTLAND PREC NO",
                  "690", 7647471.0160800004, 688344.45013000001]
        converter = crimetools.converters.Portland([COLUMN_LABELS, csvRow])
        result, total, skipped = converter.to_geojson()
        result = geojson.loads(result)

        expected_skipped = 1
        self.assertEqual(expected_skipped, skipped)

        expected_length = 0
        self.assertEqual(expected_length, len(result['features']))

    def test_convert_all(self):
        """The Converter should convert a list of CSV rows into a GeoJSON FeatureCollection"""
        csvRows = [
            COLUMN_LABELS,
            ["13807517", "12/01/2011", "01:00:00", "Liquor Laws",
             "NE WEIDLER ST and NE 1ST AVE, PORTLAND, OR 97232", "LLOYD", "PORTLAND PREC NO", "690",
             7647471.0160800004, 688344.45013000001],
            ["13716403", "07/07/2011", "18:30:00", "Liquor Laws",
             "NE SCHUYLER ST and NE 1ST AVE, PORTLAND, OR 97212", "ELIOT", "PORTLAND PREC NO",
             "590", 7647488.1558400001, 688869.34843000001]
        ]

        converter = crimetools.converters.Portland(csvRows)
        result, total, skipped = converter.to_geojson()

        expected_skipped = 0
        expected_result = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [
                            -122.66469510763777,
                            45.53435699129174
                        ],
                        "type": "Point"
                    },
                    "id": 13807517,
                    "properties": {
                        "address": "NE WEIDLER ST and NE 1ST AVE, PORTLAND, OR 97232",
                        "crimeType": "Liquor Laws",
                        "neighborhood": "LLOYD",
                        "policeDistrict": 690,
                        "policePrecinct": "PORTLAND PREC NO",
                        "reportTime": "2011-12-01T01:00:00"
                    },
                    "type": "Feature"
                },
                {
                    "geometry": {
                        "coordinates": [
                            -122.66468312170824,
                            45.53579735412487
                        ],
                        "type": "Point"
                    },
                    "id": 13716403,
                    "properties": {
                        "crimeType": "Liquor Laws",
                        "address": "NE SCHUYLER ST and NE 1ST AVE, PORTLAND, OR 97212",
                        "neighborhood": "ELIOT",
                        "policePrecinct": "PORTLAND PREC NO",
                        "policeDistrict": 590,
                        "reportTime": "2011-07-07T18:30:00"
                    },
                    "type": "Feature"
                }
            ],
            "type": "FeatureCollection"
        }

        self.assertEqual(geojson.dumps(expected_result, sort_keys=True), result)
        self.assertEqual(expected_skipped, skipped)

    def test_convert_all_skips_bad(self):
        """The Converter should skip a bad row and report it was skipped"""
        csvRows = [
            COLUMN_LABELS,
            ["13807517", "12/01/2011", "01:00:00", "Liquor Laws",
             "NE WEIDLER ST and NE 1ST AVE, PORTLAND, OR 97232", "LLOYD", "PORTLAND PREC NO", "690",
             7647471.0160800004, 688344.45013000001],
            ["13716403", "07/07/2011", "Bad Time", "Liquor Laws",
             "NE SCHUYLER ST and NE 1ST AVE, PORTLAND, OR 97212", "ELIOT", "PORTLAND PREC NO",
             "590", 7647488.1558400001, 688869.34843000001]
        ]

        converter = crimetools.converters.Portland(csvRows)
        result, total, skipped = converter.to_geojson()

        expected_skipped = 1
        expected_result = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [
                            -122.66469510763777,
                            45.53435699129174
                        ],
                        "type": "Point"
                    },
                    "id": 13807517,
                    "properties": {
                        "crimeType": "Liquor Laws",
                        "address": "NE WEIDLER ST and NE 1ST AVE, PORTLAND, OR 97232",
                        "neighborhood": "LLOYD",
                        "policePrecinct": "PORTLAND PREC NO",
                        "policeDistrict": 690,
                        "reportTime": "2011-12-01T01:00:00"
                    },
                    "type": "Feature"
                }
            ],
            "type": "FeatureCollection"
        }

        self.assertEqual(geojson.dumps(expected_result, sort_keys=True), result)
        self.assertEqual(expected_skipped, skipped)


class TestPortlandToCsv(unittest.TestCase):
    def test_converts_coordinates(self):
        """The Converter should convert coordinates in a row to WGS84"""
        csvRow = ["13807517", "12/01/2011", "01:00:00", "Liquor Laws",
                  "NE WEIDLER ST and NE 1ST AVE PORTLAND, OR 97232", "LLOYD", "PORTLAND PREC NO",
                  "690", 7647471.0160800004, 688344.45013000001]

        expected = [
            COLUMN_LABELS,
            [
                "13807517", "12/01/2011", "01:00:00", "Liquor Laws",
                "NE WEIDLER ST and NE 1ST AVE PORTLAND, OR 97232", "LLOYD", "PORTLAND PREC NO",
                "690", '-122.66469510763777', '45.53435699129174']
            ]

        converter = crimetools.converters.Portland([COLUMN_LABELS, csvRow], normalize_to_wgs84=True)

        temp = tempfile.NamedTemporaryFile(delete=False)

        if sys.version < '3':
            infile = open(temp.name, 'wb')
        else:
            infile = open(temp.name, 'w', newline='', encoding='utf8')

        temp, total, skipped = converter.to_csv(infile)
        temp.close()

        with open(temp.name, 'r') as f:
            reader = csv.reader(f)
            self.assertEqual(expected, [line for line in reader])

        os.unlink(temp.name)
