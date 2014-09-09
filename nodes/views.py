import logging
import time

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
from celery.result import AsyncResult, GroupResult
from celery.exceptions import TaskRevokedError
from celery import group
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
            hosts = request.GET.getlist('selectedhosts')
            logger.debug('Hosts: {0}'.format(hosts))
            rescmd = request.GET.getlist('cmd').pop()
            logger.info('Command: {0}'.format(rescmd))
            grouptask = group(execute_ipmi_command.s(host, rescmd) for host in hosts)()
            logger.info('Group task id: {0}'.format(grouptask.id))
            logger.info('Executing ipmi command')
            time.sleep(1)
            if grouptask.successful():
                result = grouptask.get()
                logger.info('Task executed successfully. Getting result.')
                return HttpResponse(json.dumps(result), content_type='application/json')
            else:
                request.session['taskid'] = grouptask.id
                grouptask.save()
                return HttpResponse(json.dumps({}), content_type='application/json')
        elif 'status' in request.GET:
            taskd = request.session.get('taskid')
            gtask = GroupResult.restore(taskd)
            if gtask.successful():
                try:
                    taskresult = gtask.get()
                    logger.info('Task executed successfully. Getting result.')
                    return HttpResponse(json.dumps(taskresult), content_type='application/json')
                except TaskRevokedError as excp:
                    logger.debug('Task revoked: {0} ---- {1}'.format(taskd, excp))
                    return HttpResponse({}, content_type='application/json')
            elif gtask.failed():
                logger.debug('Task failed: Id: {0}'.format(taskd))
                cancel_task(taskd)
                return HttpResponse(json.dumps({'status': 'failed'}), content_type='application/json')
            elif gtask.waiting():
                logger.info('Task waiting. Trying getting partials.')
                partials = get_partial_results(taskd)
                partials.insert(0, {'status': 'waiting'})
                logger.info('Partials: {0}'.format(partials))
                return HttpResponse(json.dumps(partials), content_type='application/json')
        elif 'cancel' in request.GET:
            tid = request.session.get('taskid')
            cancel_task(tid)
            return HttpResponse(json.dumps({}), content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})


def cancel_task(taskid):
    logger.debug('Cancelling group task: {0}'.format(taskid))
    grtask = GroupResult.restore(taskid)
    for subtask in grtask.children:
        logger.debug('Cancelling task: {0}'.format(subtask.id))
        AsyncResult(subtask.id).revoke(terminate=True, signal='KILL')


def get_partial_results(taskid):
    logger.info('Getting subtask results for group task: {0}'.format(taskid))
    grtask = GroupResult.restore(taskid)
    result = [subtask.info for subtask in grtask.children if subtask.status == 'SUCCESS']
    logger.info('Subtasks finished: {0}'.format(result))
    return result