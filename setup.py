import os

from setuptools import setup


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name='crimetools',
    description='Utilities for working with public crime data',
    long_description=read('README.md'),
    author='Andrew Brookins',
    author_email='a@andrewbrookins.com',
    url='https://github.com/abrookins/crimetools',
    version='0.2',
    packages=['crimetools'],
    install_requires=[
        'geojson==1.0.5',
        'GDAL == 1.10.0',
        'geojson == 1.0.5'
    ],
    entry_points={
        'console_scripts': [
            'crimes = crimetools.command:main',
        ]
    }
)