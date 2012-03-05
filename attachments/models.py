from StringIO import StringIO
import re

from PIL import Image

from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from south.modelsinspector import add_introspection_rules

class LongBlob(models.Field):
    def db_type(self, connection):
        return 'longblob'

add_introspection_rules([], ["^attachments\.models\.LongBlob"])

class Attachment(models.Model):
    DOCUMENT = 1
    IMAGE = 2
    TYPES = (
        (DOCUMENT, "Document"),
        (IMAGE, "Image")
    )

    JPG = 'image/jpeg'
    PNG = 'image/png'
    GIF = 'image/gif'
    PDF = 'application/pdf'
    WORD = 'application/msword'
    WORDX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    EXCEL = 'application/vnd.ms-excel'
    EXCELX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    RTF = 'text/richtext'
    BMP = 'image/x-ms-bmp'

    MIME_TYPES = (
        (JPG, 'JPEG Image'),
        (PNG, 'PNG Image'),
        (GIF, 'GIF Image'),
        (PDF, 'PDF Document'),
        (WORD, 'MS Word Document'),
        (WORDX, 'MS Word Document'),
        (EXCEL, 'Excel Document'),
        (EXCELX, 'Excel Document'),
        (RTF, 'Rich Text'),
        (BMP, 'Bitmap Image')
    )

    #This will control how the mime type is set based on file extension
    MIME_TYPE_EXTENSIONS = (
        (re.compile(r'.+?\.(?i)jpg$'), JPG),
        (re.compile(r'.+?\.(?i)jpeg$'), JPG),
        (re.compile(r'.+?\.(?i)gif$'), GIF),
        (re.compile(r'.+?\.(?i)png$'), PNG),
        (re.compile(r'.+?\.(?i)pdf$'), PDF),
        (re.compile(r'.+?\.(?i)doc$'), WORD),
        (re.compile(r'.+?\.(?i)xls$'), EXCEL),
        (re.compile(r'.+?\.(?i)docx$'), WORDX),
        (re.compile(r'.+?\.(?i)xlsx$'), EXCELX),
        (re.compile(r'.+?\.(?i)rtf'), RTF),
        (re.compile(r'.+?\.(?i)bmp'), BMP),
    )

    #This is a cross reference list to map from mimetype to attachment type
    MIME_TYPE_ATTACHMENT_TYPES = {
        JPG:IMAGE,
        PNG:IMAGE,
        GIF:IMAGE,
        PDF:DOCUMENT,
        WORD:DOCUMENT,
        EXCEL:DOCUMENT,
        WORDX:DOCUMENT,
        EXCELX:DOCUMENT,
        RTF:DOCUMENT,
        BMP:IMAGE,
    }

    #Define which model instance to attach to
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    attach_to = generic.GenericForeignKey()

    #define what is being attached
    mimetype = models.CharField(max_length=120, choices=MIME_TYPES)
    attachment_type = models.IntegerField(choices=TYPES)
    description = models.CharField(max_length=256, null=True, blank=True)
    attachment = LongBlob()
    file_name = models.CharField(max_length=256)

    #define when it was attached
    attached_at = models.DateTimeField(auto_now_add=True)

    def thumb(self):
        return self.get_attachment_url('thumbnail')

    def preview(self):
        return self.get_attachment_url('preview')

    def get_attachment_url(self, image_url):
        if self.attachment_type == self.IMAGE:
            return reverse("attachments:%s" % image_url, kwargs={'identifier':self.pk})
        elif self.mimetype == self.PDF:
            return "%simages/icons/pdf_icon.gif" % settings.MEDIA_URL
        elif self.mimetype in (self.WORD, self.WORDX):
            return "%simages/icons/DOC_icon.jpg" % settings.MEDIA_URL
        elif self.mimetype in (self.EXCEL, self.EXCELX):
            return "%simages/icons/excel_icon.gif" % settings.MEDIA_URL
        elif self.mimetype == self.RTF:
            return "%simages/icons/rtf_icon.png" % settings.MEDIA_URL

    def create_thumbnail(self, max_size):
        stream = StringIO(self.attachment)
        new_image = Image.open(stream)
        new_image.thumbnail((max_size, max_size), Image.ANTIALIAS)
        thumbnail = StringIO()
        new_image.save(thumbnail, self.mimetype.split('/')[1])
        return thumbnail.getvalue()

    def save(self, force_insert=False, force_update=False, using=None):
        if hasattr(self.attachment, 'name'):
            self.file_name = self.attachment.name

        for regex, mime_type in self.MIME_TYPE_EXTENSIONS:
            if regex.match(self.file_name):
                self.mimetype = mime_type
                self.attachment_type = self.MIME_TYPE_ATTACHMENT_TYPES[mime_type]
                break
        else:
            raise Exception(self.file_name + ' has an unsupported file type')

        if hasattr(self.attachment, 'open'):
            self.attachment.open()
            data = ''.join([chunk for chunk in self.attachment.chunks()])
            self.attachment.close()
            self.attachment = data

        super(Attachment, self).save(force_insert, force_update, using)

    @staticmethod
    def get_attachments_for(model):
        if model:
            content_type = ContentType.objects.get_for_model(model)
            return Attachment.objects.filter(content_type__pk=content_type.pk, object_id=model.pk).defer('attachment')

    @staticmethod
    def get_attachments_for_list(list_of_models):
        for model in list_of_models:
            for attachment in Attachment.get_attachments_for(model):
                yield attachment