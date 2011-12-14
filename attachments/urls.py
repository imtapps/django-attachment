from django.conf.urls.defaults import patterns, url
from attachments import views

urlpatterns = patterns('attachments',
    url(r'^thumbnail/(?P<identifier>\d+)/$', views.serve, name='thumbnail', kwargs={'action':'thumbnail'}),
    url(r'^preview/(?P<identifier>\d+)/$', views.serve, name='preview', kwargs={'action':'preview'}),
    url(r'^download/(?P<identifier>\d+)/$', views.serve, name='download', kwargs={'action':'download'}),

    url(r'^edit/$', views.edit_description, name="edit"),
    url(r'^delete/$', views.delete_attachment, name="delete"),
)
