from django import forms
from attachments import models

class RequiredAttachmentForm(forms.ModelForm):
    attachment = forms.FileField()

    def __init__(self, *args, **kwargs):
        super(RequiredAttachmentForm, self).__init__(*args, **kwargs)
        self.prefix = 'attachment'


    def save(self, model):
        return models.Attachment.objects.create(
                description=self.cleaned_data.get('description', ''),
                attach_to=model,
                attachment=self.files[self.prefix + '-attachment'])

    class Meta:
        model = models.Attachment
        #Other fields can be derived based on the model that is being attached to
        #and the item being attached
        fields = ('description', 'attachment')

    def has_description(self):
        return True if self.data.get(self.prefix + "-description") else False

class OptionalAttachmentForm(RequiredAttachmentForm):
    attachment = forms.FileField(required=False)

    def clean_attachment(self):
        if self.cleaned_data['description'] and not self.files.get(self.prefix + '-attachment'):
            raise forms.ValidationError('No file selected')

        return self.cleaned_data
