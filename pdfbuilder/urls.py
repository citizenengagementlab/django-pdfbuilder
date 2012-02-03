from django.conf.urls.defaults import *

urlpatterns = patterns(
    'pdfbuilder.views',
    
    url(r'^configuration/new/$',
        'create_configuration',
        name="create-configuration"),

    url(r'^configuration/(?P<config_id>\d+)/$',
        'configuration',
        name="view-configuration"),

    url(r'^configuration/(?P<config_id>\d+)/generate/$',
        'page_export_pdf',
        name="export-pdf"),

    url(r'^configuration/(?P<config_id>\d+)/generate/log/$',
        'prepare_pdf_export',
        name="pdf-export-log"),

    url(r'^download/(?P<pdf_id>\d+)/$',
        'download_pdf',
        name='download-pdf'),

    )
