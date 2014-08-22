import time
import logging

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import simplejson as json
from celery.exceptions import TimeoutError
from celery.result import AsyncResult

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
            res = execute_ipmi_command.apply_async((data, rescmd))
            request.session['taskid'] = res.id
            logger.info('Session taskid: {0}'.format(res.id))
            logger.info('Executing ipmi command')
            while True:
                taskstate = AsyncResult(request.session.get('taskid')).state
                logger.info('Task {0} ----> Status: {1}'.format(request.session.get('taskid'), taskstate))
                if taskstate == 'SUCCESS':
                    try:
                        outres = res.get()
                        del request.session['taskid']
                        break
                    except TimeoutError as excp:
                        logger.error('Timeout error: {0}'.format(excp))
                        time.sleep(5)
                elif taskstate == 'REVOKED':
                    del request.session['taskid']
                    outres = ''
                    break
                else:
                    print('foo: {0}'.format(taskstate))
                    logger.info('Output not ready yet. Waiting 5 seconds')
                    time.sleep(5)
            jsondata = json.dumps(outres)
            logger.info('Json: {0}'.format(jsondata))
            return HttpResponse(jsondata, content_type='application/json')
        elif 'cancel' in request.GET:
            taskid = request.session.get('taskid')
            logger.debug('Cancelling task id: {0}'.format(taskid))
            # app.control.revoke(taskid, terminate=True, signal='KILL')
            AsyncResult(taskid).revoke(terminate=True, signal='KILL')
            logger.debug('Cancelled: {0}'.format(taskid))
            return HttpResponse(json.dumps({}), content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})