from django import template
from django import forms
register = template.Library()

@register.simple_tag
def styled_field(field):
    css = 'form-select' if isinstance(field.field.widget, forms.Select) else 'form-control'
    if field.errors:
        css += ' is-invalid'
    attrs = {'class': css}
    if getattr(field.field.widget, 'input_type', '') != 'password':
        attrs['placeholder'] = field.label
    if field.errors:
        attrs['aria-invalid'] = 'true'
    descriptions = []
    if field.help_text:
        descriptions.append(field.auto_id + '_helptext')
    if field.errors:
        descriptions.append(field.auto_id + '_errors')
    if descriptions:
        attrs['aria-describedby'] = ' '.join(descriptions)
    return field.as_widget(attrs=attrs)
