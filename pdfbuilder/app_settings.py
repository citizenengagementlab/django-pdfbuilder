from django.conf import settings
import os
from pkg_resources import resource_filename

try:
    PDFBUILDER_COVERLETTER_CSS = settings.PDFBUILDER_COVERLETTER_CSS
except AttributeError:
    PDFBUILDER_COVERLETTER_CSS = os.path.abspath(
        resource_filename("pdfbuilder", "pisa-default.css"))

try:
    PDFBUILDER_COVERLETTER_TEMPLATE = settings.PDFBUILDER_COVERLETTER_TEMPLATE
except AttributeError:
    PDFBUILDER_COVERLETTER_TEMPLATE = """
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head><body>%s</body></html>"""
