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

RESULT = {}


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
            rescmd = request.GET.getlist('cmd').pop()
            execute_ipmi_command(data, rescmd)
            jsondata = json.dumps(RESULT)
            return HttpResponse(jsondata, content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})


def do_command(result, ipmisession):
    if 'error' in result:
        print('Error for node {0}'.format(ipmisession.bmc))
        return
    command_ = IPMICMD
    if command_ == 'status':
        value = ipmisession.get_power()
        RESULT[ipmisession.bmc] = {command_: value.get('powerstate')}
    elif command_ == 'up':
        pass
    elif command_ == 'down':
        pass


def execute_ipmi_command(host_list, ipmicommand):
    global IPMICMD
    IPMICMD = ipmicommand
    for host in host_list:
        ipmisession = command.Command(host, 'admin', 'admin', onlogon=do_command)
    ipmisession.eventloop()