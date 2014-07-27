from django.http import HttpResponse
from django.shortcuts import render
from nodes.models import Site, Node
from django.core import serializers


"""
class IndexView(generic.ListView):
    template_name = "nodes/index.html"
    context_object_name = "sites_list"

    def get_queryset(self):

        Return all the sites.

        return Site.objects.all()

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["data"] = self.get_queryset()
        return context
"""


def index(request):
    if request.is_ajax():
        if "name" in request.GET:
            name = request.GET.get("name")
            if name == "all":
                wnodes = Node.objects.all()
            else:
                wnodes = Node.objects.filter(site__sitename__exact=name)
            json_ = serializers.serialize('json', wnodes, fields=['hostname', 'ip'])
            return HttpResponse(json_, content_type="application/json")
        elif 'selectedhosts[]' in request.GET.keys():
            copy = request.GET.copy()
            # res = execute_ipmi_command(copy.values())
            return render(request, 'nodes/index.html', {'result': copy.values()})
    else:
        sites = Site.objects.all()
        return render(request, "nodes/index.html", {"listsites": sites})


def execute_ipmi_command(host_list):
    for host in host_list:
        print host
    return 'OK'