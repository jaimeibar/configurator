from __future__ import absolute_import
from socket import gaierror

from celery import shared_task
from celery.utils.log import get_task_logger
from celery.states import FAILURE
from celery.exceptions import TimeoutError
from pyghmi.ipmi import command
from pyghmi.exceptions import IpmiException

from nodes.utils import get_hostname_from_ip, get_ip_from_hostname


logger = get_task_logger(__name__)


def set_task_failed(self, *args, **kwargs):
    logger.error('Task execution failed: Aborting.')
    self.update_state(state=FAILURE)


@shared_task(bind=True, on_failure=set_task_failed)
def execute_ipmi_command(self, host, ipmicommand):
    result = {}
    try:
        ipmisession = command.Command(host, 'admin', 'admin')
        ipmisess = True
    except gaierror as excp:
        logger.error('Error in ipmisession. Hostname: {0} -> {1}'.format(host, excp))
        hostip = get_ip_from_hostname(host)
        logger.info('Trying with ip {0}'.format(hostip))
        try:
            ipmisession = command.Command(hostip, 'admin', 'admin')
            ipmisess = True
        except IpmiException as excp:
            logger.error('Error in ipmisession. Hostname: {0} - IP: {1} -> {2}'.format(host, hostip, excp))
            ipmisess = False
    except IpmiException as excp:
        logger.error('Error in ipmisession: host {0} -> {1}'.format(host, excp))
        ipmisess = False
    if ipmisess:
        if ipmicommand == 'status':
            value = ipmisession.get_power()
        elif ipmicommand == 'up':
            logger.info('Executing command {0} in {1}'.format(ipmicommand, host))
            value = ipmisession.set_power('on', wait=True)
        elif ipmicommand == 'down':
            logger.info('Executing command {0} in {1}'.format(ipmicommand, host))
            value = ipmisession.set_power('off', wait=True)
        logger.info('Executing OK for {0}'.format(host))
        if not host.isalnum():
            host = get_hostname_from_ip(hostip)
        result[host] = {'power': value.get('powerstate')}
    else:
        raise TimeoutError
    return result