import os.path
import logging
from logging.handlers import RotatingFileHandler

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import simplejson as json
from pyghmi.ipmi import command
from pyghmi.exceptions import IpmiException

from nodes.models import Site, Node


RESULT = {}
logger = logging.getLogger(os.path.basename(__name__))


def configure_logger():
    """
    Config for logging messages.
    """
    # Set up a specific logger with our desired output level
    logger.setLevel(logging.DEBUG)
    # Create a rotating file handler
    handler = RotatingFileHandler("configurator.log", maxBytes=1000000, backupCount=10)
    # Add the log message handler to the logger
    logger.addHandler(handler)
    # create formatter
    message = "[%(asctime)s] [%(levelname)s] %(message)s"
    time_format = "%a %b %d %H:%M:%S %Y"
    log_format = logging.Formatter(message, time_format)
    # Add format to the handler
    handler.setFormatter(log_format)


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
        ipmisession = command.Command(host, 'admin', 'admin', onlogon=do_command)
    ipmisession.eventloop()