from django import template
register = template.Library()
# from mongobase.models import admin_stuff

@register.inclusion_tag('mongobase/connection.html')
def status():
    # return {"status":(admin_stuff.objects.filter(id=1)[0]).database_status}
    return {"status":True}