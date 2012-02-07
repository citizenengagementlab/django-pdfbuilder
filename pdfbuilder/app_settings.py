from django.conf import settings
import os
from pkg_resources import resource_filename
from zope.dottedname import resolve as dottedname

try:
    PDFBUILDER_COVERLETTER_CSS = settings.PDFBUILDER_COVERLETTER_CSS
except AttributeError:
    PDFBUILDER_COVERLETTER_CSS = os.path.abspath(
        resource_filename("pdfbuilder", "pisa-default.css"))

try:
    PDFBUILDER_COVERLETTER_FUNCTION = settings.PDFBUILDER_COVERLETTER_FUNCTION
except AttributeError:
    PDFBUILDER_COVERLETTER_FUNCTION = 'pdfbuilder.coverletter.default_coverletter_function'
PDFBUILDER_COVERLETTER_FUNCTION = dottedname.resolve(PDFBUILDER_COVERLETTER_FUNCTION)
