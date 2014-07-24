from django.contrib import admin
from nodes.models import Site, Node


class HostnameInLine(admin.TabularInline):
    model = Node
    extra = 1


class SiteAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Site Name", {"fields": ["sitename"]}),
        ("Details", {"fields": ["location", "description"], "classes": ["collapse"]}),
    ]
    inlines = [HostnameInLine]
    list_display = ["sitename", "location", "description"]
    list_filter = ["sitename"]
    search_fields = ["sitename"]
    ordering = ["sitename"]


admin.site.register(Site, SiteAdmin)