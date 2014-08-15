from __future__ import absolute_import

from celery import shared_task
from pyghmi.ipmi import command
from pyghmi.exceptions import IpmiException
from socket import gaierror

from nodes.views import get_ip_from_hostname, get_hostname_from_ip
from nodes.views import logger


@shared_task
def execute_ipmi_command(host_list, ipmicommand):
    result = {}
    for host in host_list:
        try:
            ipmisession = command.Command(host, 'admin', 'admin')
        except gaierror as e:
            logger.error('Error in ipmisession: host {0} - {1}'.format(host, e))
            hostip = get_ip_from_hostname(host)
            logger.info('Trying with ip {0}'.format(hostip))
            try:
                ipmisession = command.Command(hostip, 'admin', 'admin')
            except IpmiException as e:
                logger.error('Error in ipmisession: host {0} - {1}'.format(host, e))
        except IpmiException as e:
            logger.error('Error in ipmisession: host {0} - {1}'.format(host, e))
        if ipmisession:
            if ipmicommand == 'status':
                value = ipmisession.get_power()
            if not host.isalnum():
                host = get_hostname_from_ip(hostip)
            result[host] = {'power': value.get('powerstate')}