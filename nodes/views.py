import os.path
import logging
from socket import gaierror

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import simplejson as json
from pyghmi.ipmi import command

from nodes.models import Site, Node


RESULT = {}
logger = logging.getLogger(os.path.basename(__name__))


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
        elif 'selectedhosts' in request.GET.keys():
            data = request.GET.getlist('selectedhosts')
            rescmd = request.GET.getlist('cmd').pop()
            execute_ipmi_command(data, rescmd)
            jsondata = json.dumps(RESULT)
            return HttpResponse(jsondata, content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})


def do_command(result, ipmisession):
    logger.info('foo')
    if 'error' in result:
        print('Error for node {0}'.format(ipmisession.bmc))
        return
    command_ = IPMICMD
    if command_ == 'status':
        value = ipmisession.get_power()
    elif command_ == 'up':
        value = ipmisession.set_power('on', wait=True)
    elif command_ == 'down':
        value = ipmisession.set_power('off', wait=True)
    RESULT[ipmisession.bmc] = {'power': value.get('powerstate')}


def execute_ipmi_command(host_list, ipmicommand):
    global IPMICMD
    IPMICMD = ipmicommand
    for host in host_list:
        try:
            ipmisession = command.Command(host, 'admin', 'admin', onlogon=do_command)
        except gaierror as e:
            logger.error('Error in ipmisession: host {0} - {1}'.format(host, e))
            ipmisession = False
    if ipmisession:
        ipmisession.eventloop()