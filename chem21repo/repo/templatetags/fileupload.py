from django import template

register = template.Library()

@register.inclusion_tag('repo/fileupload.html')
def fileupload_form(id, target_pk=None, target_type="question", caption="Upload media ...", upload_url=None):
    return {'id':id, 'target_pk': target_pk, 'target_type':target_type, 'button_caption': caption, 'upload_url': upload_url}
    
