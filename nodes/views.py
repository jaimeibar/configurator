import logging

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
from celery.result import AsyncResult
from celery.exceptions import TaskRevokedError
import simplejson as json

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
            logger.info('Task id: {0}'.format(res.id))
            logger.info('Executing ipmi command')
            request.session['taskid'] = res.id
            return HttpResponse(json.dumps({}), content_type='application/json')
        elif 'status' in request.GET:
            taskd = request.session.get('taskid')
            m = AsyncResult(taskd)
            if m.successful():
                try:
                    taskresult = m.get()
                    return HttpResponse(json.dumps(taskresult), content_type='application/json')
                except TaskRevokedError as excp:
                    logger.debug('Task revoked: {0} ---- {1}'.format(taskd, excp))
                    return HttpResponse({}, content_type='application/json')
            elif m.failed():
                logger.debug('Task failed: {0} -> {1}'.format(taskd, m.state))
                return HttpResponse(json.dumps({'status': 'failed'}), content_type='application/json')
            return HttpResponse(json.dumps({}), content_type='application/json')
        elif 'cancel' in request.GET:
            tid = request.session.get('taskid')
            logger.debug('Cancelling task: {0}'.format(tid))
            AsyncResult(tid).revoke(terminate=True, signal='KILL')
            return HttpResponse(json.dumps({}), content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})
