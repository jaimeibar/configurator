import logging
import time

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
from celery.result import AsyncResult, GroupResult
from celery.exceptions import TaskRevokedError
from celery.states import PENDING, FAILURE
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
                # GroupTask id
                request.session['taskid'] = grouptask.id
                # Subtasks id's of the GroupTask
                request.session[grouptask.id] = [taid.id for taid in grouptask.subtasks]
                return HttpResponse(json.dumps({}), content_type='application/json')
        elif 'status' in request.GET:
            result = []
            gtaskid = request.session.get('taskid')
            stids = request.session.get(gtaskid)
            for stask in stids:
                res = check_subtask_status(stask)
                if isinstance(res, dict):
                    logger.info('Getting result for task: {0}'.format(stask))
                    result.append(res)
                    stids.remove(stask)
                elif res == FAILURE:
                    logger.info('Removing subtask from list: {0}'.format(stask))
                    cancel_task(stask)
                    stids.remove(stask)
            if not result:
                logger.info('No subtasks have finished yet')
            else:
                logger.info('Subtasks finished: {0} ---- {1}'.format(result, len(result)))
            logger.info('Subtasks remaining: {0}'.format(len(stids)))
            if not stids:
                result.insert(0, {'status': 'complete'})
                logger.info('Task executed successfully.')
                return HttpResponse(json.dumps(result), content_type='application/json')
            request.session[gtaskid] = stids
            return HttpResponse(json.dumps(result), content_type='application/json')
        elif 'cancel' in request.GET:
            gtaskid = request.session.get('taskid')
            subtasks = request.session.get(gtaskid)
            cancel_task(subtasks)
            return HttpResponse(json.dumps({}), content_type='application/json')
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})


def cancel_task(taskid):
    # Taskid is an subtasks id's list
    for stask in taskid:
        logger.debug('Cancelling subtask: {0}'.format(stask))
        AsyncResult(stask).revoke(terminate=True, signal='KILL')


def check_subtask_status(subtaskid):
    logger.info('Checking subtask: {0}'.format(subtaskid))
    tk = AsyncResult(subtaskid)
    if tk.successful():
        logger.info('Subtask finished: {0}'.format(subtaskid))
        try:
            return tk.get()
        except TaskRevokedError as excp:
            logger.debug('Task revoked: {0} ---- {1}'.format(subtaskid, excp))
    elif tk.state == PENDING:
        logger.info('Subtask not finished yet: {0}'.format(subtaskid))
        return PENDING
    elif tk.state == FAILURE:
        logger.info('Subtask failed: {0}'.format(subtaskid))
        return FAILURE