from django import forms
from django.core.exceptions import ValidationError
from attachments import models

class RequiredAttachmentForm(forms.ModelForm):
    attachment = forms.FileField()

    def __init__(self, *args, **kwargs):
        super(RequiredAttachmentForm, self).__init__(*args, **kwargs)
        self.prefix = 'attachment'

    def clean(self):
        if self._uploaded_file and not self.instance.get_mime_type(self._uploaded_file.name):
            raise ValidationError("{} has an unsupported file type".format(self._uploaded_file.name))

        return self.cleaned_data

    @property
    def _uploaded_file(self):
        name = self.prefix + '-attachment'
        return self.files[name] if name in self.files else None

    def save(self, model):
        return models.Attachment.objects.create(
            attach_to=model,
            description=self.cleaned_data.get('description', None),
            attachment=self._uploaded_file,
            tag=self.cleaned_data.get('tag', None),
        )

    class Meta:
        model = models.Attachment
        fields = ('description', 'attachment')

    def has_description(self):
        return True if self.data.get(self.prefix + "-description") else False

class OptionalAttachmentForm(RequiredAttachmentForm):
    attachment = forms.FileField(required=False)

    def clean_attachment(self):
        if self.cleaned_data['description'] and not self.files.get(self.prefix + '-attachment'):
            raise forms.ValidationError('No file selected')

        return self.cleaned_data

class TaggedAttachmentForm(RequiredAttachmentForm):
    tag = forms.CharField(required=True)

    class Meta(RequiredAttachmentForm.Meta):
        fields = RequiredAttachmentForm.Meta.fields + ('tag', )
