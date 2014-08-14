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
        elif 'selectedhosts' in request.GET:
            data = request.GET.getlist('selectedhosts')
            logger.debug('Data: {0}'.format(data))
            rescmd = request.GET.getlist('cmd').pop()
            logger.info('Command: {0}'.format(rescmd))
            execute_ipmi_command(data, rescmd)
            logger.info('Executing ipmi command')
            jsondata = json.dumps(RESULT)
            logger.info('Json: {0}'.format(jsondata))
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
    if not host.isalnum():
        host = get_hostname_from_ip(host)
    RESULT[host] = {'power': value.get('powerstate')}


def execute_ipmi_command(host_list, ipmicommand):
    RESULT.clear()
    global IPMICMD
    IPMICMD = ipmicommand
    for host in host_list:
        try:
            ipmisession = command.Command(host, 'admin', 'admin', onlogon=do_command)
            ipmisess = True
        except gaierror as e:
            logger.error('Error in ipmisession: host {0} - {1}'.format(host, e))
            hostip = get_ip_from_hostname(host)
            logger.info('Trying with ip {0}'.format(hostip))
            try:
                ipmisession = command.Command(hostip, 'admin', 'admin', onlogon=do_command)
            except IpmiException as e:
                logger.error('Error in ipmisession: host {0} - {1}'.format(host, e))
                ipmisess = False
            ipmisess = True
        except IpmiException as e:
            logger.error('Error in ipmisession: host {0} - {1}'.format(host, e))
            ipmisess = False
    if ipmisess:
        ipmisession.eventloop()


def get_ip_from_hostname(hostame):
    hostn = hostame + '.aragrid.es'
    ip = Node.objects.filter(hostname__exact=hostn).values_list('ip', flat=True).first()
    return ip


def get_hostname_from_ip(hostip):
    hname = Node.objects.filter(ip__exact=hostip).values_list('hostname', flat=True).first()
    shname = hname.split('.', 1)[0]
    return shname
