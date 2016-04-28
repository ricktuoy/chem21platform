from django import template

register = template.Library()

@register.inclusion_tag('repo/media_upload.html')
def media_upload_button(id):
    return {'id':id}
    
