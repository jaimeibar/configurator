from django.http import HttpResponse
from django.shortcuts import render
from nodes.models import Site, Node
from django.core import serializers
import simplejson as json
from pyghmi.ipmi import command


"""
class IndexView(generic.ListView):
    template_name = "nodes/index.html"
    context_object_name = "sites_list"

    def get_queryset(self):

        Return all the sites.

        return Site.objects.all()

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["data"] = self.get_queryset()
        return context
"""


def index(request):
    if request.is_ajax():
        if "name" in request.GET:
            name = request.GET.get("name")
            if name == "all":
                wnodes = Node.objects.all()
            else:
                wnodes = Node.objects.filter(site__sitename__exact=name)
            json_ = serializers.serialize('json', wnodes, fields=('hostname', 'ip'))
            return HttpResponse(json_, content_type="application/json")
        elif 'selectedhosts[]' in request.GET.keys():
            data = request.GET.getlist('selectedhosts[]')
            res = execute_ipmi_command(data)
            jsondata = json.dumps(res)
            return HttpResponse(jsondata, content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})


def execute_ipmi_command(host_list):
    for host in host_list:
        ipmicmd = command.Command(host, 'admin', 'admin', onlogon=do_command)
        print(ipmicmd)

def do_command(result, ipmisession):
    command_ = 'power'
    if command_ == 'power':
        value = ipmisession.get_power()
        return value