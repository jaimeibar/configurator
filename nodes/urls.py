from django.conf.urls import patterns, url
from nodes import views

urlpatterns = patterns('',
                       # url(r'^$', views.IndexView.as_view(), name="index"),
                       url(r'^$', "nodes.views.index", name="index"),
                       )