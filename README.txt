django-pdfbuilder builds PDFs from your data.  It provides:

* A Python library for generating PDFs from objects by providing an
  abstraction layer over Reportlab 

* A framework for developing consistent PDF "templates" with fine-grained
  control over layouts, styles, and object-to-PDF rules

* A web application for managing generated PDFs and configuration 
  templates


Installation
============

1) pip install django-pdfbuilder

2) Add "pdfbuilder" to your Django project's ``INSTALLED_APPS``

3) Configure a data source function in ``settings.PDFBUILDER_DATA_SOURCE``
   (see below)

4) manage.py syncdb

5) Register some PDF configuration templates (see below)


Data Sources
============

A data source is a function that returns a Django queryset which can
be used to generate PDFs.  For example:

  def my_pdf_data_source(request, data_source_key=None):
    return MyModel.objects.all()

The "data_source_key" argument will be a string provided by the end user.
You can use this to provide different subsets of data, or even data from
different models, for different requests.

After you have written a data source function, reference it by dotted name
in your ``settings.py`` file.  For example, if the above function was placed
in a ``myapp/pdfbuilder_settings.py`` file, you would write:

  PDFBUILDER_DATA_SOURCE = "myapp.pdfbuilder_settings.my_pdf_data_source"

in your ``settings.py`` file.


Defining available data sources for the end user
------------------------------------------------

By default, when generating a PDF, the end user will be presented with
a simple freeform text input where he can specify the "data_source_key"
that he wants to use.

You can override this user interface element to provide a fixed set of
available data_source keys by overriding the template

  ``pdfbuilder/snippets/pdf_export_form_data_source.html``

with your own HTML.


Cover Letter
============

The end user can specify a cover letter that will be prepended to the
PDF.  The user should input the cover letter in Markdown format.  It
will be converted to HTML (using the markdown library) and then to a
PDF (using the pisa/xhtml2pdf library) and will then be merged with
the primary output PDF (using the pyPdf library) when that PDF has
been saved.

There is a pisa CSS stylesheet that is used to control the font sizes,
margins and other styling options for the cover letter.  It is in
`pdfbuilder/pisa-default.css` and is set to use the same fonts and
margins as the primary output PDF.

TODO: make the CSS file be TTW-managed content?


PDF Grouping Options
====================

PDFs can be "grouped", meaning multiple PDFs will be generated from
the given options.  For example, if you are generating PDFs from
``django.contrib.comments`` objects, you could group comments by
their ``content_object`` properties, and generate a distinct PDF
for each content object that has received comments.

To register a new grouping option::

  from pdfbuilder import registry
  registry.register_grouping(grouping_fn, string_id, text_description)

It will then appear as an option in the PDF configuration form.  You
should do this registration somewhere that will be guaranteed to be
imported early, like an INSTALLED_APP's ``models.py``.

Each grouping_fn should be a function with signature ``(buckets, entry)``
that will be called for each model instance from your data source, before
it is used to build an entry in the PDF output.  The ``buckets`` argument
is a stateful dict of lists-of-instances, grouped according to which PDF 
they will be put into.

The job of the grouping_fn is threefold:

 * Figure out what group the given signature belongs to
 * Create an empty list entry in the ``buckets`` dict if the
   appropriate group does not exist 
 * Return the string key of the group that the signature belongs to

This dict will then be used to determine how many distinct PDFs to
create, and which PDF each signature belongs to.  The string keys that
your grouping_fn creates in the ``buckets`` dict will also be used to
identify each distinct PDF to the end user.

Note that at the moment each entry can only be in one bucket.

A default grouping_fn (which groups all entries into a single PDF) and
its registration can be found in ``pdfbuilder/registry.py``.


PDF Sort Order Options
======================

To register a new sort order::

  from pdfbuilder import registry
  registry.register_ordering(tuple, string_id, text_description)

It will then appear as an option in the PDF configuration form.  You
should do this registration somewhere that will be guaranteed to be
imported early, like an INSTALLED_APP's ``models.py``.

The "tuple" argument should be a tuple of Django `order_by` args, that
is, one or more strings that reference columns on the model you are
pulling data from. For example, if you are generating PDFs from
``django.contrib.comments`` objects, valid sorting registrations would
include::

  registry.register_ordering(('site__name',),
			     "site", "Order alphabetically by name of associated site")
  registry.register_ordering(('user__last_name', 'user__first_name', 'user_name'),
			     "name", "Order alphabetically by name of commenter")
  registry.register_ordering(('-submit_date'),
                             "date", "Order comments from most recent to earliest")


PDF Filter Options
==================

Registering a new filtering option is done simply by overriding the 
template ``pdfbuilder/snippets/configuration_form_filters.html`` and
adding an additional HTML checkbox for the filter you want to add.

The checkbox's value should correspond to a method defined on the
model class of your data source.  This method will be called to
determine whether a given entry should be included or omitted from the
generated PDF.  The entry will be omitted if and only if the specified
method returns ``None``.  (Specifically ``None``, not any false value;
if the method returns an empty string, this will not be sufficient to
omit it.)

So, to add a new filtering option, you may need to add a new method to
your data-source model classes that performs whatever query you want to
filter by.

TODO: register arbitrary filter functions instead


PDF Layout Templates
====================

To register a new template::

  from pdfbuilder import registry
  registry.register_template(TemplateClass, string_id, text_description)

It will then appear as an option in the PDF configuration form.  You
should do this registration somewhere that will be guaranteed to be
imported early, like an INSTALLED_APP's ``models.py``.

A set of sample general-purpose templates and their registrations are defined
in ``pdfbuilder/sampletemplates.py``.  To use these, import them with

  from pdfbuilder import sampletemplates

in your own code.  Alternatively, you can provide your own PDF template classes
and register them instead.

Your PDF template class should be a subclass of
``pdfbuilder.basetemplates.PDFTemplate`` which implements the
``generate_flowable_from_entry`` classmethod.  Basically, this method is called
for each model instance in your data source, and is expected to return a 
ReportLab "flowable" that will be rendered in the PDF document.
(See ``pdfbuilder/sampletemplates.py`` for examples.)

For most layouts, implementing this method should be sufficient.  You
might need to customize other things though.

Changing the Platypus Doctemplate
---------------------------------

By default, PDFTemplates use a subclass of
``reportlab.platypus.SimpleDocTemplate`` to build their PDFs.  This
subclass provides configurable page header and footer functionality.

You can customize the ``reportlab.platypus`` DocTemplate used by your
``PDFTemplate`` by setting a class attribute ``doctemplatefactory``.
See ``pdfbuilder.sampletemplates:ThreeColumnDown`` as an example.
This template uses a non-default doctemplate which defines a
three-column newspaper-style layout.

If you need to customize the initialization of a doctemplate (as well
as its definition) you can override the classmethod
``PDFTemplate.doctemplate`` to provide custom logic.  This method
receives a ``pdfbuilder.models.Configuration`` object which you can use
to determine how to initialize the doctemplate.

Changing the Entry-Numbering Style
----------------------------------

Your PDFTemplate subclass can override ``PDFTemplate.entry_prefix`` to
customize the display of entry numbers.  It takes a boolean
``should_number_entries`` argument determined by configuration; you
should make sure to respect this by returning an empty string if it is
``False``.

Changing the PDF Stylesheet
---------------------------

You can override the ``PDFTemplate.get_stylesheet`` classmethod to return
a custom ReportLab stylesheet for your template.  See the sample templates
in ``pdfbuilder/sampletemplates.py`` for examples.

Post-Processing the Flowables
-----------------------------

You may need to manipulate the list of ReportLab Flowables after they have
been generated but before they are handed off to ReportLab.  To do this,
implement the classmethod ``post_generate_flowables`` on your PDFTemplate 
subclass.  For an example look at ``pdfbuilder.sampletemplates:ThreeColumnAcross``
which implements this method to wrap all flowables in a Reportlab Table flowable.
