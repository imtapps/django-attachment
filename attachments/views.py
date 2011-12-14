from django import http
from attachments import models

class ImageServer(object):

    def __init__(self, attachment):
        self.attachment = attachment

    def download(self):
        return self.attachment.attachment

    def preview(self):
        return self.attachment.create_thumbnail(max_size=550)

    def thumbnail(self):
        return self.attachment.create_thumbnail(max_size=100)

def serve(request, action, identifier):
    attachment = models.Attachment.objects.get(pk=identifier)

    image_server = ImageServer(attachment)
    file_to_serve = getattr(image_server, action)()

    return http.HttpResponse(file_to_serve, mimetype=attachment.mimetype)

def edit_description(request):
    if 'description' in request.REQUEST and 'id' in request.REQUEST:
        attachment = models.Attachment.objects.get(pk=request.REQUEST['id'])
        attachment.description = request.REQUEST['description']
        attachment.save()

    return http.HttpResponse("success")

def delete_attachment(request):
    if 'id' in request.REQUEST:
        attachment = models.Attachment.objects.get(pk=request.REQUEST['id'])
        attachment.delete()
    return http.HttpResponse("success")
