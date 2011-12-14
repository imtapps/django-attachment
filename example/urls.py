from django.conf.urls.defaults import patterns, include, url
from django import http
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from attachments.forms import OptionalAttachmentForm
from attachments.models import Attachment
from sample_app.models import Person

def create(request):
    form = OptionalAttachmentForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        form.save(Person.objects.create())
        return http.HttpResponseRedirect("/")

    context = dict(
        form=form,
        attachments=Attachment.objects.all()
    )

    return render_to_response("main/form.html", context, context_instance=RequestContext(request))

urlpatterns = patterns('',
    url(r'^attachments/', include('attachments.urls', namespace="attachments")),
    url(r'^$', create, name="create")
)

