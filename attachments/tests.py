from django import test
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.urlresolvers import reverse
from mock import Mock, patch
import mock

from attachments.models import Attachment
from sample_app.models import First, Second
from attachments import forms
from attachments import views

class AttachmentTests(test.TestCase):

    def test_be_able_to_add_attachment_to_a_model_instance(self):
        model = First.objects.create(first_field="asdf", second_field="xyz")
        Attachment.objects.create(file_name="x.doc", attach_to=model, attachment_type=Attachment.DOCUMENT,
                                  attachment="Hi there, i'm a bunch of bytes")
        self.assertEqual(Attachment.objects.count(), 1)

    def test_be_able_to_add_attachment_to_different_model_instance(self):
        model = Second.objects.create(third_field="asdf")
        Attachment.objects.create(file_name="x.doc", attach_to=model, attachment_type=Attachment.DOCUMENT,
                                  attachment="Hi there, i'm another bunch of bytes")
        self.assertEqual(Attachment.objects.count(), 1)

    def test_be_able_to_attach_multiple_items_to_a_single_model_instance(self):
        model = Second.objects.create(third_field="xyz")
        Attachment.objects.create(file_name="x.doc", attach_to=model, attachment_type=Attachment.DOCUMENT,
                                  attachment="first bunch of something")
        Attachment.objects.create(file_name="x.doc", attach_to=model, attachment_type=Attachment.DOCUMENT,
                                  attachment="second bunch of something")
        self.assertEqual(Attachment.objects.count(), 2)

    def test_be_able_to_get_attachments_for_model_instance(self):
        second = Second.objects.create(third_field="xyz")
        Attachment.objects.create(file_name="x.doc", attach_to=second,
                                  attachment="first bunch of something")
        Attachment.objects.create(file_name="x.doc", attach_to=second,
                                  attachment="second bunch of something")

        first = First.objects.create(first_field="asdf", second_field="xyz")
        Attachment.objects.create(file_name="x.doc", attach_to=first, attachment_type=Attachment.DOCUMENT,
                                  attachment="Hi there, i'm a bunch of bytes")

        for attachment in Attachment.get_attachments_for(second):
            self.assertEqual(attachment.attach_to, second)

        self.assertEqual(Attachment.get_attachments_for(second).count(), 2)

    def test_store_attachment_description(self):
        second = Second.objects.create(third_field="xyz")
        Attachment.objects.create(file_name="x.doc", attach_to=second, attachment="xxx",
                                  attachment_type=Attachment.DOCUMENT, description="Three x's")
        self.assertEqual(Attachment.get_attachments_for(second).count(), 1)

    @patch('attachments.models.Attachment.get_attachments_for', Mock())
    def test_get_attachment_for_model_for_each_model_in_list_in_get_attachments_for_list(self):
        first_model, second_model = Mock(), Mock()
        attachment = Mock()
        Attachment.get_attachments_for.return_value = [attachment]
        result = list(Attachment.get_attachments_for_list([first_model, second_model]))
        self.assertEqual([
            ((first_model,), {}),
            ((second_model,), {}),
        ], Attachment.get_attachments_for.call_args_list)

        self.assertEqual([attachment] * 2, result)

    def test_save_timestamp_when_attachment_is_added(self):
        second = Second.objects.create(third_field="xyz")
        Attachment.objects.create(file_name="x.doc", attach_to=second, attachment_type=Attachment.DOCUMENT,
                                  attachment="xxx", description="Three x's")
        attachment = Attachment.objects.get(pk=1)
        self.assertEqual(attachment.attached_at.__class__.__name__, 'datetime')

    def test_save_mime_type_when_attachment_is_added(self):
        second = Second.objects.create(third_field="xyz")
        Attachment.objects.create(file_name="x.pdf", attach_to=second, attachment="xxx",
                                  description="Three x's")
        attachment = Attachment.objects.get(pk=1)
        self.assertEqual(attachment.mimetype, 'application/pdf')

    def test_save_type_of_attachment(self):
        second = Second.objects.create(third_field="xyz")
        Attachment.objects.create(file_name="x.doc", attach_to=second,
                                  attachment="xxx",
                                  mimetype="text/plain",
                                  description="Three x's",
                                  attachment_type=Attachment.DOCUMENT)
        attachment = Attachment.objects.get(pk=1)
        self.assertEqual(attachment.attachment_type, Attachment.DOCUMENT)

    def test_raise_exception_for_unsupported_file_types(self):
        second = Second.objects.create(third_field="xyz")
        self.assertRaises(Exception, Attachment.objects.create, file_name="something.xml",
                                      attach_to=second, attachment="here is a dummy image blob....")

    def test_tell_if_form_has_description(self):
        form = forms.OptionalAttachmentForm({'attachment-description': "abc"})
        self.assertEqual(True, form.has_description())
        form = forms.OptionalAttachmentForm()
        self.assertEqual(False, form.has_description())

    #
    #   These tests are attachment type specific (ie: jpg, doc, pdf...)
    #

    def test_does_not_raise_validation_error_for_valid_mime_type(self):
        second = Second.objects.create(third_field="xyz")

        model = Attachment(
            file_name="something.jpg",
            description="alsdkfj",
            mimetype="image/jpeg",
            attachment_type=1,
            attach_to=second,
            attachment="here is a dummy image blob...."
        )

        self.assertEqual(None, model.full_clean())

    @patch('attachments.models.Attachment.create_thumbnail', Mock(return_value=None))
    def test_derive_mime_type_and_attachment_type_for_jpg(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.jpg",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.JPG)
        self.assertEqual(a.attachment_type, Attachment.IMAGE)
        self.assertEqual(a.thumb(), reverse("attachments:thumbnail", args=[a.pk]))

        a = Attachment.objects.create(file_name="something.jpeg",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.JPG)
        self.assertEqual(a.attachment_type, Attachment.IMAGE)
        self.assertEqual(a.thumb(), reverse("attachments:thumbnail", args=[a.pk]))

    @patch('attachments.models.Attachment.create_thumbnail', Mock(return_value=None))
    def test_derive_mime_type_and_attachment_type_for_png(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.png", attach_to=second,
                                      attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.PNG)
        self.assertEqual(a.attachment_type, Attachment.IMAGE)
        self.assertEqual(a.thumb(), reverse("attachments:thumbnail", args=[a.pk]))

    @patch('attachments.models.Attachment.create_thumbnail', Mock(return_value=None))
    def test_derive_mime_type_and_attachment_type_for_gif(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.gif",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.GIF)
        self.assertEqual(a.attachment_type, Attachment.IMAGE)
        self.assertEqual(a.thumb(), reverse("attachments:thumbnail", args=[a.pk]))

    def test_derive_mime_type_and_attachment_type_for_word(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.doc",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.WORD)
        self.assertEqual(a.attachment_type, Attachment.DOCUMENT)
        self.assertEqual(a.thumb(), "%simages/icons/DOC_icon.jpg" % settings.MEDIA_URL)

    def test_derive_mime_type_and_attachment_type_for_word_x(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.docx",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.WORDX)
        self.assertEqual(a.attachment_type, Attachment.DOCUMENT)
        self.assertEqual(a.thumb(), "%simages/icons/DOC_icon.jpg" % settings.MEDIA_URL)

    def test_derive_mime_type_and_attachment_type_for_excel(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.xls",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.EXCEL)
        self.assertEqual(a.attachment_type, Attachment.DOCUMENT)
        self.assertEqual(a.thumb(), "%simages/icons/excel_icon.gif" % settings.MEDIA_URL)

    def test_derive_mime_type_and_attachment_type_for_excel_x(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.xlsx",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.EXCELX)
        self.assertEqual(a.attachment_type, Attachment.DOCUMENT)
        self.assertEqual(a.thumb(), "%simages/icons/excel_icon.gif" % settings.MEDIA_URL)

    def test_derive_mime_type_and_attachment_type_for_pdf(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.pdf",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.PDF)
        self.assertEqual(a.attachment_type, Attachment.DOCUMENT)
        self.assertEqual(a.thumb(), "%simages/icons/pdf_icon.gif" % settings.MEDIA_URL)

    def test_derive_mime_type_and_attachment_type_for_rtf(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.rtf",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.RTF)
        self.assertEqual(a.attachment_type, Attachment.DOCUMENT)
        self.assertEqual(a.thumb(), "%simages/icons/rtf_icon.png" % settings.MEDIA_URL)

    @patch('attachments.models.Attachment.create_thumbnail', Mock(return_value=None))
    def test_derive_mime_type_and_attachment_type_for_bmp(self):
        second = Second.objects.create(third_field="xyz")
        a = Attachment.objects.create(file_name="something.bmp",
                                      attach_to=second, attachment="here is a dummy image blob....")
        self.assertEqual(a.mimetype, Attachment.BMP)
        self.assertEqual(a.attachment_type, Attachment.IMAGE)
        self.assertEqual(a.thumb(), reverse("attachments:thumbnail", args=[a.pk]))

    def test_require_attachment_value_when_description_is_present(self):
        form = forms.OptionalAttachmentForm({'attachment-description':"somefile.doc"}, {'attachment-attachment':''})
        self.assertFalse(form.is_valid())

    def test_require_attachment_when_description_is_present(self):
        form = forms.OptionalAttachmentForm({'attachment-description':"somefile.doc"})
        self.assertFalse(form.is_valid())

    def test_form_is_valid_when_instance_has_valid_mime_type(self):
        file = Mock()
        file.name = "asdf.jpg"
        files = {'attachment-attachment': file}
        form = forms.RequiredAttachmentForm(data={}, files=files)
        self.assertEqual(True, form.is_valid())

    def test_require_attachment_when_using_required_attachment_form(self):
        form = forms.RequiredAttachmentForm({})
        self.assertFalse(form.is_valid())

    def test_not_require_attachment_when_using_optional_attachment_form(self):
        form = forms.OptionalAttachmentForm({})
        self.assertTrue(form.is_valid())

    @patch('__builtin__.super', Mock())
    @patch('attachments.models.Attachment.create_thumbnail')
    def test_not_create_thumbnail_when_not_image_type_in_save(self, create_thumbnail):
        attached_file = Mock()
        attached_file.name = "image.doc"
        attached_file.chunks.return_value = []
        Attachment(attachment=attached_file).save()
        self.assertEqual(0, create_thumbnail.call_count)

    @patch('attachments.models.StringIO')
    @patch('attachments.models.Image')
    def test_open_image_with_stringio_of_attachment_in_create_thumbnail(self, image_class, stringio):
        attachment = Attachment(attachment=Mock())
        attachment.mimetype = "x/y"
        attachment.create_thumbnail(max_size=100)
        self.assertEqual(((attachment.attachment,), {}), stringio.call_args_list[0])
        image_class.open.assert_called_once_with(stringio.return_value)

    @patch('attachments.models.Image')
    def test_create_thumbnail_with_dimensions_and_image_mode_in_create_thumbnail(self, image):
        attachment = Attachment(attachment=Mock())
        attachment.mimetype = "x/y"
        attachment.create_thumbnail(max_size=100)
        image.open.return_value.thumbnail.assert_called_once_with((100, 100), image.ANTIALIAS)

    @patch('attachments.models.Image')
    def test_create_thumbnail_with_given_dimensions_and_image_mode_in_create_thumbnail(self, image):
        attachment = Attachment(attachment=Mock())
        attachment.mimetype = "x/y"
        attachment.create_thumbnail(max_size=2)
        image.open.return_value.thumbnail.assert_called_once_with((2, 2), image.ANTIALIAS)

    @patch('attachments.models.StringIO')
    @patch('attachments.models.Image')
    def test_save_image_and_return_stream_in_create_thumbnail(self, image, stringio):
        attachment = Mock()
        attachment = Attachment(attachment=attachment)
        attachment.mimetype = "attachment/pdf"
        thumbnail = attachment.create_thumbnail(max_size=100)
        image.open.return_value.save.assert_called_once_with(stringio.return_value, 'pdf')
        self.assertEqual(stringio.return_value.getvalue.return_value, thumbnail)

    @patch('attachments.models.reverse')
    def test_return_attachments_url_for_images_in_get_sample_url(self, _reverse):
        instance = Mock(spec=Attachment())
        instance.attachment_type = instance.IMAGE
        view_name = "some_view_name"
        url = Attachment.get_attachment_url(instance, view_name)
        _reverse.assert_called_once_with("attachments:%s" % view_name, kwargs={'identifier': instance.pk})
        self.assertEqual(_reverse.return_value, url)

    def test_call_get_attachment_url_with_thumbnail_in_thumb(self):
        instance = Mock(spec=Attachment())
        Attachment.thumb(instance)
        instance.get_attachment_url.assert_called_once_with("thumbnail")

    def test_call_get_attachment_url_with_preview_in_preview(self):
        instance = Mock(spec=Attachment())
        Attachment.preview(instance)
        instance.get_attachment_url.assert_called_once_with("preview")


class AttachmentViewTests(test.TestCase):

    @patch('attachments.views.ImageServer', Mock())
    @patch('attachments.models.Attachment.objects')
    def test_get_attachment_object_in_serve(self, attachment_manager):
        identifier = Mock()
        views.serve(Mock(), str(Mock()), identifier)
        attachment_manager.get.assert_called_once_with(pk=identifier)

    @patch('attachments.views.ImageServer')
    @patch('attachments.models.Attachment.objects')
    def test_create_image_server_with_attachment_in_serve(self, attachment_manager, image_server):
        attachment = Mock()
        attachment_manager.get.return_value = attachment
        views.serve(Mock(), str(Mock()), Mock())
        image_server.assert_called_once_with(attachment)

    @patch('attachments.models.Attachment.objects', Mock())
    @patch('attachments.views.ImageServer')
    def test_call_action_on_image_server(self, image_server):
        views.serve(Mock(), 'test', Mock())
        self.assertEqual(True, image_server.return_value.test.called)

    @patch('django.http.HttpResponse')
    @patch('attachments.models.Attachment.objects.get')
    @patch('attachments.views.ImageServer')
    def test_return_http_response_with_action_response_and_mimetype(self, image_server, get_attachment, response):
        identifier = Mock()
        result = views.serve(Mock(), 'test', identifier)

        attachment = get_attachment.return_value
        file_to_serve = image_server.return_value.test.return_value
        response.assert_called_once_with(file_to_serve, mimetype=attachment.mimetype)
        self.assertEqual(response.return_value, result)

class ImageServerTests(test.TestCase):

    def setUp(self):
        self.attachment = Mock()
        self.image_server = views.ImageServer(self.attachment)

    def test_set_attachment_on_init(self):
        self.assertEqual(self.image_server.attachment, self.attachment)

    def test_return_attached_file_in_download(self):
        self.assertEqual(self.image_server.download(), self.attachment.attachment)

    def test_return_thumbnail_from_preview(self):
        result = self.image_server.preview()
        self.attachment.create_thumbnail.assert_called_once_with(max_size=550)
        self.assertEqual(result, self.attachment.create_thumbnail.return_value)

    def test_return_thumbnail_from_thumbnail(self):
        result = self.image_server.thumbnail()
        self.attachment.create_thumbnail.assert_called_once_with(max_size=100)
        self.assertEqual(result, self.attachment.create_thumbnail.return_value)

class AttachmentFormTests(test.TestCase):

    def test_clean_raises_validation_error_when_instance_has_invalid_mime_type(self):
        file = Mock()
        file.name = "asdf.zip"
        files = {'attachment-attachment': file}
        form = forms.RequiredAttachmentForm(data={}, files=files)
        with self.assertRaises(ValidationError) as validation:
            form.clean()
        self.assertEquals(file.name + " has an unsupported file type", validation.exception.messages[0])

    def test_tagged_attachment_form_is_subclass_of_required_attachment_form(self):
        self.assertTrue(issubclass(forms.TaggedAttachmentForm, forms.RequiredAttachmentForm))

    def test_tagged_attachment_form_requires_tag_field(self):
        form = forms.TaggedAttachmentForm({})
        self.assertEqual('This field is required.', form.errors['tag'][0])

    def test_tagged_attachment_form_contains_tag_field(self):
        self.assertIn('tag', forms.TaggedAttachmentForm._meta.fields)

    def test_tagged_attachment_form_contains_description_field(self):
        self.assertIn('description', forms.TaggedAttachmentForm._meta.fields)

    def test_tagged_attachment_form_contains_attachment_field(self):
        self.assertIn('attachment', forms.TaggedAttachmentForm._meta.fields)
