from setuptools import setup, find_packages
import sys, os

version = '0.1'

long_description = ""

setup(name='django-pdfbuilder',
      version=version,
      description="Generate PDFs from data sources according to managed configurations and extensible templates",
      long_description=long_description,
      classifiers=[], 
      keywords='',
      author='Ethan Jucovy',
      author_email='ethan.jucovy@gmail.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "djangohelpers",
        "html5lib",
        "markdown",
        "pisa",
        "pyPdf",
        "ReportLab",
        "tailer",
        "zope.dottedname",
        ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
