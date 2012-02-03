from pdfbuilder import registry
from pdfbuilder.basetemplates import BaseDocTemplateWithHeaderAndFooter as BaseDocTemplate
from pdfbuilder.basetemplates import OneColumnBaseDocTemplateWithHeaderAndFooter as OneColumnDocTemplate
from pdfbuilder.basetemplates import PDFTemplate

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

import random

class ThreeColumnDown(PDFTemplate):
    doctemplatefactory = BaseDocTemplate

    @classmethod
    def get_stylesheet(cls):
        style = getSampleStyleSheet()['Normal']
        style.spaceAfter = style.fontSize
        return style


class ThreeColumnAcross(PDFTemplate):

    @classmethod
    def generate_flowable_from_entry(cls, entry, entry_prefix, stylesheet, bucket):
        try:
            row = bucket[-1]
        except IndexError: # it's an empty list
            row = []
            bucket.append(row)
        if len(row) == 3: 
            # If the row is full (has 3 elements already) we make a new row
            row = []
            bucket.append(row)

        data = "%s%s" % (entry_prefix, str(entry))
        row.append(Paragraph(data, stylesheet))

    @classmethod
    def post_generate_flowables(cls, flowables_buckets):
        style = TableStyle([
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LINEBELOW", (0,0), (-1,-1), 1, colors.gray),
                ("LINEABOVE", (0,0), (-1,0), 1, colors.gray),
                ])
        tables = {}
        for key, rows in flowables_buckets.items():
            t = Table(rows)
            t.setStyle(style)
            tables[key] = [t]
        return tables


class OneColumn(PDFTemplate):    
    doctemplatefactory = OneColumnDocTemplate

    @classmethod
    def get_stylesheet(cls):
        styles = getSampleStyleSheet()
        styles['Heading1'].spaceAfter = 12
        styles['Heading1'].fontName = "Helvetica"
        return styles['Heading1']


registry.register_template(ThreeColumnDown, "threecolumn_down",
                           "Three column layout, flowing down the page (newspaper style)")
registry.register_template(ThreeColumnAcross, "threecolumn_across",
                           "Three column layout, filling data across in rows with lines separating the rows")
registry.register_template(OneColumn, "onecolumn_withcomments",
                           "One column layout")
