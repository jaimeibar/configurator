from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', 'django.contrib.auth.views.login', {'template_name': 'nodes/login.html'}),
    url(r'^index/', include("nodes.urls", namespace="index")),
)