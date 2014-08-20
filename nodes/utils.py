from nodes.models import Node


def get_ip_from_hostname(hostame):
    hostn = ''.join((hostame, '.aragrid.es'))
    ip = Node.objects.filter(hostname__exact=hostn).values_list('ip', flat=True).first()
    return ip


def get_hostname_from_ip(hostip):
    hname = Node.objects.filter(ip__exact=hostip).values_list('hostname', flat=True).first()
    shname = hname.split('.', 1)[0]
    return shname
