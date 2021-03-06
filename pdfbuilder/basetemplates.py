import random
from reportlab.lib import colors
from reportlab.lib import pagesizes
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, BaseDocTemplate
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.platypus import Frame, PageTemplate
import tempfile

class ReportlabProgressLogger(object):
    def __init__(self, logger):
        self.logger = logger
        self.size_est = None

    def __call__(self, type, value):
        if type == "SIZE_EST":
            self.size_est = value
        elif type == "PROGRESS":
            if value % 500:
                return
            print >> self.logger, "Building PDF from flowables: %s / %s" % (
                value, self.size_est)
            self.logger.flush()

class _DocTemplateWithHeaderAndFooter(object):
    def beforePage(self):
        if self.pageheader is None:
            return
        canvas = self.canv
        canvas.drawCentredString(canvas._pagesize[0] / 2.0, 
                                 canvas._pagesize[1] - 0.5*inch, self.pageheader)

    def afterPage(self):
        if self.pagefooter is None:
            return
        canvas = self.canv
        canvas.drawCentredString(canvas._pagesize[0] / 2.0, 0.5*inch, self.pagefooter)

class FancyFrame(Frame):

    def add(self, flowable, canvas, trySplit=0):
        result = Frame.add(self, flowable, canvas, trySplit=trySplit)
        if result == 0:
            return result
        
        # Slight hack: we're assuming that trySplit==0 iff this flowable
        # is an already-split portion of another flowable. So we don't want
        # to draw a line below it, since it's not the end of an entry.
        # This assumes that this frame's parent doctemplate allowSplitting
        # has not been changed from the default.
        if trySplit == 0:
            return result

        canvas.saveState()
        canvas.setStrokeColor(colors.gray)
        fudge = flowable.getSpaceAfter() / 2.0
        canvas.line(self._x, self._y + fudge, self._x + self.width, self._y + fudge)
        canvas.restoreState()
        return result

class BaseDocTemplateWithHeaderAndFooter(_DocTemplateWithHeaderAndFooter, BaseDocTemplate):
    def __init__(self, *args, **kw):
        BaseDocTemplate.__init__(self, *args, **kw)

        doc = self
        columns = []
        interFrameMargin = 0.2*inch
        frameWidth = doc.width / 3 - interFrameMargin
        columns.append(FancyFrame(doc.leftMargin, doc.bottomMargin, frameWidth, doc.height))
        columns.append(FancyFrame(doc.leftMargin + frameWidth + interFrameMargin, 
                             doc.bottomMargin, frameWidth, doc.height))
        columns.append(FancyFrame(doc.leftMargin + 2 * frameWidth + 2 * interFrameMargin,
                             doc.bottomMargin, frameWidth, doc.height))
        
        #doc.showBoundary = True
        doc.addPageTemplates([
                PageTemplate(id='ThreeColumn', frames=columns),
                ])


class OneColumnBaseDocTemplateWithHeaderAndFooter(_DocTemplateWithHeaderAndFooter, 
                                                  BaseDocTemplate):
    def __init__(self, *args, **kw):
        BaseDocTemplate.__init__(self, *args, **kw)

        doc = self
        columns = []
        columns.append(FancyFrame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height))
        
        #doc.showBoundary = True
        doc.addPageTemplates([
                PageTemplate(id='OneColumn', frames=columns),
                ])

## Be careful of MRO here -- we need to make sure that
##   _DocTemplateWithHeaderAndFooter.beforePage has precedence
##   over SimpleDocTemplate.beforePage
class SimpleDocTemplateWithHeaderAndFooter(_DocTemplateWithHeaderAndFooter, SimpleDocTemplate):
    def __init__(self, *args, **kw):
        SimpleDocTemplate.__init__ (self, *args, **kw)

class PDFTemplate(object):
    """
    Base class for objects that implement PDF "templates" or layouts.
    """

    doctemplatefactory = SimpleDocTemplateWithHeaderAndFooter

    _pdf_fd = None
    _pdf_filename = None

    def reset_pdf_file(self):
        self._pdf_fd = None
        self._pdf_filename = None

    def pdf_file(self):
        if self._pdf_fd is not None and self._pdf_filename is not None:
            return self._pdf_fd, self._pdf_filename
        fd, filename = tempfile.mkstemp(suffix=".pdf")
        self._pdf_fd = fd
        self._pdf_filename = filename
        return self._pdf_fd, self._pdf_filename

    def doctemplate(self, config):
        fd, filename = self.pdf_file()

        template = self.doctemplatefactory(
            filename, pagesize=pagesizes.letter)
        template.pageheader = config.header()
        template.pagefooter = config.footer()

        return template

    def canvasmaker(self, config):
        if config.number_pages():
            return NumberedCanvas
        return canvas.Canvas

    def get_stylesheet(self):
        return getSampleStyleSheet()['Normal']

    def generate_flowables(self, entries,
                           number_entries=True, 
                           bucket_selector=None, log_callback=None):

        stylesheet = self.get_stylesheet()
        entry_prefixes = {}
        flowables_buckets = {}

        self.pre_generate_flowables(entries)

        for entry in entries:
            bucket_key = bucket_selector(flowables_buckets, entry)
            flowables_bucket = flowables_buckets[bucket_key]
            entry_prefix = entry_prefixes.setdefault(
                bucket_key, self.entry_prefix(number_entries))

            flowable = self.generate_flowable_from_entry(entry, entry_prefix, stylesheet, 
                                                         flowables_bucket)
            if flowable is not None:
                flowables_bucket.append(flowable)

            if log_callback:
                log_callback(flowables_buckets)
        
        return self.post_generate_flowables(flowables_buckets)

    def pre_generate_flowables(self, entries):
        pass

    def post_generate_flowables(self, flowables_buckets):
        return flowables_buckets

    def generate_flowable_from_entry(self, entry, entry_prefix, stylesheet, bucket):
        """
        Implement in a subclass.  Should return a reportlab flowable
        to be passed to ``doctemplate.build``.

        Alternatively you may need to generate multiple flowables for a single
        entry, or do other odd things.  In that case you can append your new
        flowables directly to the ``bucket`` within your implementation,
        and return None to signal that the calling code should not try to append
        anything.
        """
        return Paragraph("%s%s" % (entry_prefix, str(entry)), stylesheet)

    def entry_prefix(self, should_number_entries):
        if should_number_entries:
            return "<seq id='%d'/>. " % random.randint(0, 10000)
        return ''

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 7)
        self.drawRightString(200*mm, 20*mm,
            "Page %d of %d" % (self._pageNumber, page_count))
