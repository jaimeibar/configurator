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
                taskid = request.session.get('taskid')
                if request.session.get(taskid):
                    subtasksids = request.session.get(taskid)
                else:
                    grtask = GroupResult.restore(taskid)
                    subtasksids = [taid.id for taid in grtask.subtasks]
                partialsres, tasksrem = get_partial_results(subtasksids)
                partialsres.insert(0, {'status': 'waiting'})
                logger.info('Partials: {0}'.format(partialsres))
                if tasksrem:
                    request.session[taskid] = tasksrem
                return HttpResponse(json.dumps(partialsres), content_type='application/json')
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


def get_partial_results(subtasks):
    results = []
    logger.info('Subtasks remaining: {0}'.format(len(subtasks)))
    logger.info('Subtasks list: {0}'.format(subtasks))
    for subtaskid in subtasks:
        tk = AsyncResult(subtaskid)
        if tk.successful():
            logger.info('Subtask finished. Adding to results: {0}'.format(subtaskid))
            results.append(tk.get())
            logger.info('Deleting subtask from subtasks list: {0}'.format(subtaskid))
            subtasks.remove(subtaskid)
    if subtasks:
        logger.info('Subtasks not finished yet: {0}'.format(len(subtasks)))
        logger.info('Subtasks not finished yet: {0}'.format(subtasks))
        return results, subtasks
    else:
        logger.info('Subtasks finished: {0}'.format(results))
        return results