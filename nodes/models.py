# -*- coding: utf-8 -*-

from django.db import models


class Site(models.Model):
    sitename = models.CharField(max_length=50, null=False, unique=True)
    location = models.CharField(max_length=200, null=True)
    description = models.TextField(max_length=400, null=True)

    def __unicode__(self):
        return self.sitename


class Subnet(models.Model):
    site = models.ForeignKey(Site)
    subnet = models.IntegerField(max_length=1)
    description = models.TextField(max_length=400, null=True)

    def __unicode__(self):
        return str(self.subnet)


class Node(models.Model):
    subnet = models.ForeignKey(Subnet)
    site = models.ForeignKey(Site)
    hostname = models.CharField(max_length=40)
    ip = models.IPAddressField()
    description = models.TextField(max_length=400, null=True)

    def __unicode__(self):
        return self.hostname