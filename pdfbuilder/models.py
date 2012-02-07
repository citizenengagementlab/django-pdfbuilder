from ConfigParser import RawConfigParser
from ConfigParser import NoOptionError, NoSectionError
from django.contrib.auth import models as auth
from django.db import models
from StringIO import StringIO

class _NoDefault(object):
    def __repr__(self):
        return "(no default)"
NoDefault = _NoDefault()
del _NoDefault

class Configuration(models.Model):
    name = models.TextField()
    data = models.TextField()

    @models.permalink
    def get_absolute_url(self):
        return ('view-configuration', [str(self.pk)])

    def __unicode__(self):
        return str(self.name or self.pk)

    def set_options(self, kwargs):
        config = RawConfigParser()
        fp = StringIO(self.data)
        config.readfp(fp)

        for key, val in kwargs.items():
            if key == "filter_by":
                if val is None:
                    config.remove_option("options", "filter_by")
                else:
                    config.set("options", key, " ".join(val))
            else:
                config.set("options", key, val)

        fp = StringIO()
        config.write(fp)
        fp.seek(0)
        self.data = fp.read()
        self.save()

    def get_option(self, key, default=NoDefault, asbool=False):
        config = RawConfigParser()
        fp = StringIO(self.data)

        config.readfp(fp)
        try:
            value = config.get("options", key)
        except (NoOptionError, NoSectionError):
            if default is NoDefault:
                raise
            return default

        if not asbool:
            return value.strip()

        value = value.lower()
        if value in ("1", "true", "t", "yes", "y", "on"):
            return True
        elif value in ("0", "false", "f", "no", "n", "off"):
            return False
        else:
            raise TypeError("Cannot convert to bool: %s" % value)

    def filter_by(self):
        filters = self.get_option("filter_by", "")
        return filters.split()
        
    def order_by(self):
        return self.get_option("order_by", "none").lower()

    def group_by(self):
        return self.get_option("group_by", "none").lower()

    def header(self):
        return self.get_option("header", None)

    def footer(self):
        return self.get_option("footer", None)

    def number_entries(self):
        return self.get_option("entrynumbers", default=False, asbool=True)

    def number_pages(self):
        return self.get_option("pagenumbers", default=False, asbool=True)

    def template(self):
        return self.get_option("template", "threecolumn_down")

    def load_template(self):
        from pdfbuilder import registry
        return registry.get_template(self.template())

class SavedPdf(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    configuration = models.ForeignKey(Configuration)
    author = models.ForeignKey(auth.User)
    file = models.FileField(upload_to="pdfs/%Y/%m/%d")
    comment = models.TextField(null=True, blank=True)
    cover_letter = models.TextField(null=True, blank=True)
    
    # Store the key of the "grouping" of each PDF, 
    # e.g. 'default' (if no grouping) or 
    # e.g. "CT" or "MD" (if grouping by state) .. etc
    group = models.TextField()

    data_source = models.TextField()

    @models.permalink
    def get_absolute_url(self):
        return ('download-pdf', [str(self.pk)])

