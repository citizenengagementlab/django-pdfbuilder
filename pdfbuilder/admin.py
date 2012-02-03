from django.contrib import admin
from pdfbuilder.models import Configuration, SavedPdf

class ConfigAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'number_pages', 'number_entries',
                    'order_by', 'filter_by',
                    'header', 'footer',
                    'template')

class PdfAdmin(admin.ModelAdmin):
    list_display = ('created', 'configuration', 'author', 'comment')
    list_filter = ('created', 'configuration', 'author')
    search_fields = ['comment']

admin.site.register(Configuration, ConfigAdmin)
admin.site.register(SavedPdf, PdfAdmin)
