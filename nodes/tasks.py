from __future__ import absolute_import

from celery import shared_task

from pyghmi.ipmi import command


@shared_task
def execute_ipmi_command(hostlist, ipmicommand):
    for host in hostlist:
        command.Command(host, 'admin', 'admin')