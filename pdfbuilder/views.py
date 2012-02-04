import datetime
from django.conf import settings
from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from djangohelpers import allow_http
from djangohelpers import rendered_with
import ho.pisa as pisa
import markdown
import os
import pprint
import pyPdf
from reportlab.pdfgen import canvas
import sys
import tailer
import tempfile

from pdfbuilder.basetemplates import (NumberedCanvas,
                                      ReportlabProgressLogger)
from pdfbuilder.models import (Configuration,
                               SavedPdf)
from pdfbuilder import registry
from pdfbuilder import app_settings

@rendered_with("pdfbuilder/new_configuration.html")
@allow_http("GET", "POST")
def create_configuration(request):
    if request.method == "GET":
        return {}

    data = "[options]"
    name = "New Configuration by %s on %s" % (
        request.user.username, datetime.datetime.now())

    if 'clone_from' in request.POST:
        try:
            base_config = Configuration.objects.get(
                pk=request.POST['clone_from'])
        except Configuration.DoesNotExist:
            pass
        else:
            data = base_config.data
            name = "Copy of <%s>" % base_config.name
            name = "%s by %s on %s" % (
                name, 
                request.user.username, 
                datetime.datetime.now())

    config = Configuration()
    config.data = data
    config.name = name
    config.save()
    url = reverse("view-configuration", args=[config.id])
    qs = []
    if 'data_source' in request.POST:
        qs.append("data_source=%s" % request.POST['data_source'])
    if len(qs):
        qs = '&'.join(qs)
        url += "?" + qs
    return HttpResponseRedirect(url)

@rendered_with("pdfbuilder/configuration.html")
@allow_http("GET", "POST")
def configuration(request, config_id):
    config = get_object_or_404(Configuration, pk=config_id)

    if request.method == "GET":
        saved_pdfs = SavedPdf.objects.filter(configuration=config)
        return {
            'config': config,
            'templates': registry.available_templates(),
            'orderings': registry.available_orderings(),
            'groupings': registry.available_groupings(),
            'saved_pdfs': saved_pdfs,
            }

    options = dict(request.POST.items())
    if 'csrfmiddlewaretoken' in request.POST:
        del options['csrfmiddlewaretoken']
    if 'description' in request.POST:
        config.name = options['description']
        del options['description']
    if 'filter_by' in request.POST and request.POST['filter_by'].strip():
        options['filter_by'] = request.POST.getlist("filter_by")
    else:
        options['filter_by'] = None

    url = reverse("view-configuration", args=[config.id])
    qs = []
    if 'data_source' in request.GET:
        qs.append("data_source=%s" % request.GET['data_source'])
    if len(qs):
        qs = '&'.join(qs)
        url += "?" + qs

    config.set_options(options)
    return HttpResponseRedirect(url)

@allow_http("GET", "POST")
def prepare_pdf_export(request, config_id):
    if request.method == "POST":
        fd, filename = tempfile.mkstemp(suffix=".log")
        fp = open(filename, 'w')
        print >> fp, "Ready to start PDF generation"
        fp.close()
        
        # Strip off the path and the suffix
        filename = filename[len(tempfile.gettempdir()):]
        filename = filename[:-4]
        filename = filename.lstrip(os.path.sep)
        assert os.sep not in filename and filename.isalnum() # lazy security checking
        return HttpResponse(filename, content_type="text/plain")

    filename = request.GET.get("key")
    assert filename and os.sep not in filename and filename.isalnum() # lazy security checking
    filename = os.path.join(tempfile.gettempdir(), filename + ".log")
    fp = open(filename)
    try:
        body = tailer.tail(fp, 1)[0]
    except IndexError:
        body = ''
    fp.close()
    return HttpResponse(body, content_type="text/plain")

@allow_http("GET", "POST")
@rendered_with("pdfbuilder/pdf_export.html")
def page_export_pdf(request, config_id):
    config = get_object_or_404(Configuration, pk=config_id)
    if request.method == "GET":
        return {'config': config}

    log_filename = request.POST.get("key")
    assert (log_filename and os.sep not in log_filename
            and log_filename.isalnum()) # lazy security checking
    log_filename = os.path.join(tempfile.gettempdir(),
                                log_filename + ".log")

    data_source = request.POST.get("data_source")

    logger = open(log_filename, 'w')
    print >> logger, "Fetching data from source.."
    logger.flush()

    from zope.dottedname.resolve import resolve
    queryset = resolve(settings.PDFBUILDER_DATA_SOURCE)(request, data_source)

    entry_count_upper_bound = queryset.count()

    order_by = registry.get_ordering(config.order_by())
    if order_by is not None:
        queryset = queryset.order_by(*order_by)

    group_by = registry.get_grouping(config.group_by())
    
    filter_by = config.filter_by()
    ## FIXME: this is ugly
    def fixer(queryset, filter_by):
        for item in queryset:
            omit = False
            for field in filter_by:
                if getattr(item, field)() is None:
                    omit = True
                    break
            if omit is True:
                continue
            yield item
    queryset = fixer(queryset, filter_by)

    template = registry.get_template(config.template())

    def log_callback(prepared_flowables):
        count = 0
        for name, bucket in prepared_flowables.items():
            count += len(bucket)
        if count % 500:
            return
        print >> logger, "%s / %s" % (count, entry_count_upper_bound)
        logger.flush()

    try:
        grouped_elements = template.generate_flowables(
            queryset,
            number_entries=config.number_entries(),
            bucket_selector=group_by,
            log_callback=log_callback)
    except Exception, e:
        print >> logger, pprint.pformat(sys.exc_info())
        logger.flush()
        raise

    cover_letter = request.POST.get('coverletter')
    if cover_letter:
        print >> logger, "Generating cover letter..."
        logger.flush()
        _default_css = open(app_settings.PDFBUILDER_COVERLETTER_CSS)
        DEFAULT_CSS = _default_css.read()
        _default_css.close()
        del(_default_css)
        cover_letter = markdown.markdown(cover_letter)
        cover_letter = app_settings.PDFBUILDER_COVERLETTER_HTML % cover_letter.encode("utf8")
        fd, cover_letter_filename = tempfile.mkstemp(suffix=".pdf")
        cover_letter_file = open(cover_letter_filename, 'wb')
        pisa.CreatePDF(cover_letter, cover_letter_file, default_css=DEFAULT_CSS)
        cover_letter_file.close()

    print >> logger, "Finalizing %s PDF(s)..." % len(grouped_elements)
    logger.flush()

    comment = request.POST.get("comment", '')

    progress_logger = ReportlabProgressLogger(logger)
    saved_pdfs = []
    for key, elements in grouped_elements.items():
        template.reset_pdf_file()
        doc = template.doctemplate(config)
        doc.setProgressCallBack(progress_logger)
        doc.build(elements, canvasmaker=template.canvasmaker(config))

        fd, filename = template.pdf_file()

        if cover_letter:
            print >> logger, "Merging cover letter with PDF..."
            logger.flush()
            cover_letter_file = open(cover_letter_filename)
            cover_letter = pyPdf.PdfFileReader(cover_letter_file)
            content_file = open(filename)
            content = pyPdf.PdfFileReader(content_file)
            result = pyPdf.PdfFileWriter()
            for page in cover_letter.pages:
                result.addPage(page)
            for page in content.pages:
                result.addPage(page)

            fd, result_filename = tempfile.mkstemp(suffix=".pdf")

            fp = open(result_filename, 'wb')
            result.write(fp)

            cover_letter_file.close()
            content_file.close()
            fp.close()

            os.unlink(cover_letter_filename)
            os.unlink(filename)
            filename = result_filename

        fp = open(filename)

        print >> logger, "Storing PDF file and updating database..."
        logger.flush()

        pdf = SavedPdf(author=request.user, 
                       configuration=config,
                       comment=comment,
                       data_source=data_source,
                       group=key,
                       cover_letter=request.POST.get('coverletter', ''))
        file = File(fp)
        pdf.file.save("%s-%s.pdf" % (config.pk, request.user), file)
        file.close()
        os.unlink(filename)
        del(fd)
        saved_pdfs.append(pdf)
    
    print >> logger, "PDF generation complete."
    logger.flush()
    logger.close()
    os.unlink(log_filename)

    return pdf_table_snippet(request, saved_pdfs) 

@rendered_with("pdfbuilder/snippets/pdf_table.html")
def pdf_table_snippet(request, saved_pdfs):
    return {'saved_pdfs': saved_pdfs}

def download_pdf(request, pdf_id):
    pdf = SavedPdf.objects.get(pk=pdf_id)
    contents = pdf.file.read()
    resp = HttpResponse(contents,
                        content_type="application/pdf")
    resp['Content-Disposition'] = "attachment; filename=export.pdf"
    return resp
