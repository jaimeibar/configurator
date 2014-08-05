import os.path
import logging
from socket import gaierror

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import simplejson as json
from pyghmi.ipmi import command
from pyghmi.exceptions import IpmiException

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
            logger.debug('Data: {0}'.format(data))
            rescmd = request.GET.getlist('cmd').pop()
            execute_ipmi_command(data, rescmd)
            jsondata = json.dumps(RESULT)
            return HttpResponse(jsondata, content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})


def do_command(result, ipmisession):
    host = ipmisession.bmc
    logger.info('Executing session for {0}'.format(host))
    if 'error' in result:
        logger.error('Error {0} in node {1}'.format(result.get('error'), host))
        return
    command_ = IPMICMD
    logger.info('Command: {0}'.format(command_))
    if command_ == 'status':
        try:
            logger.info('Executing command {0} in {1}'.format(command_, host))
            value = ipmisession.get_power()
        except IpmiException as e:
            logger.error('Error executing command {0} in {1}: {2}'.format(command_, host, e))
            return
    elif command_ == 'up':
        logger.info('Executing command {0} in {1}'.format(command_, host))
        value = ipmisession.set_power('on', wait=True)
    elif command_ == 'down':
        logger.info('Executing command {0} in {1}'.format(command_, host))
        value = ipmisession.set_power('off', wait=True)
    logger.info('Executing OK for {0}'.format(host))
    RESULT[host] = {'power': value.get('powerstate')}


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