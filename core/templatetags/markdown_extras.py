import markdown
from django import template

register = template.Library()

@register.filter(name="markdownify")
def markdownify(text):
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables"]
    )