import time
import logging

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import simplejson as json
from celery.exceptions import TimeoutError

from nodes.models import Site, Node
from nodes.tasks import execute_ipmi_command


logger = logging.getLogger(__name__)


def index(request):
    if request.is_ajax():
        if 'name' in request.GET:
            name = request.GET.get('name')
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
            res = execute_ipmi_command.delay(data, rescmd)
            time.sleep(1)
            logger.info('Executing ipmi command')
            while True:
                if res.state == 'SUCCESS':
                    try:
                        outres = res.get()
                        break
                    except TimeoutError as excp:
                        logger.error('Timeout error: {0}'.format(excp))
                        time.sleep(5)
                else:
                    logger.info('Output not ready yet. Waiting 5 seconds')
                    time.sleep(5)
            jsondata = json.dumps(outres)
            logger.info('Json: {0}'.format(jsondata))
            return HttpResponse(jsondata, content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})