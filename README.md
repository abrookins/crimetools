# crimetools: Utilities for working with public crime data

This package includes various utilities to convert public crime data into friendlier formats,
including from state-specific coordinate systems into WGS84 and from CSV into GeoJSON.

# Installing

Download the package and run `python setup.py install` or `python setup.py develop`.

# Using

    pdxcrime_to_geojson {input_filename} {output_filename}

If you omit the output file, the file will be {intput_filename}.json.

# License

See LICENSE.
