from django import template

register = template.Library()

@register.inclusion_tag('repo/fileupload.html')
def fileupload_form(id, cap="Upload media ..."):
    return {'id':id, 'button_caption': cap}
    
