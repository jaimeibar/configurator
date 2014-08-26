import logging
import os
import os.path
import glob

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
            with open(os.path.join('/tmp', 'session-{0}'.format(res.id)), 'w') as session:
                session.write(res.id)
                session.close()
            logger.info('Executing ipmi command')
            if res:
                try:
                    jsondata = json.dumps(res.get())
                    logger.info('Json: {0}'.format(jsondata))
                    return HttpResponse(jsondata, content_type='application/json')
                except TaskRevokedError as excp:
                    logger.debug('Task revoked: {0} ---- {1}'.format(res.id, excp))
                    return HttpResponse({}, content_type='application/json')
            else:
                logger.info('Task not finished yet')
                return HttpResponse({}, content_type='application/json')
        elif 'cancel' in request.GET:
            logger.debug('Cancelling task')
            tid = glob.glob(os.path.join('/tmp', 'session-*')).pop()
            with open(tid) as sess:
                t = sess.read().strip()
                sess.close()
            AsyncResult(t).revoke(terminate=True, signal='KILL')
            os.unlink(tid)
            return HttpResponse(json.dumps({}), content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})
