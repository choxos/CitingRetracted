import json
from datetime import date, datetime
from django import template
from django.utils.safestring import mark_safe
from urllib.parse import urlencode

register = template.Library()

@register.filter
def map(queryset, field_name):
    """
    Extract a specific field from each object in a queryset/list.
    Usage: {{ queryset|map:"field_name" }}
    """
    try:
        if not queryset:
            return []
        
        result = []
        for obj in queryset:
            if hasattr(obj, field_name):
                value = getattr(obj, field_name)
                result.append(value)
            elif isinstance(obj, dict) and field_name in obj:
                result.append(obj[field_name])
        
        return result
    except Exception as e:
        # Return empty list if something goes wrong
        return []

@register.filter
def safe_json(value):
    """
    Safely serialize a value to JSON, handling None values and other edge cases
    that might cause JavaScript syntax errors.
    """
    def json_serializer(obj):
        """Custom JSON serializer for datetime and other objects"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif obj is None:
            return None
        return str(obj)
    
    try:
        # Ensure the value is not None
        if value is None:
            return mark_safe('null')
        
        # Handle empty lists and dicts
        if isinstance(value, list) and not value:
            return mark_safe('[]')
        if isinstance(value, dict) and not value:
            return mark_safe('{}')
        
        # Serialize with custom serializer
        json_str = json.dumps(value, default=json_serializer, ensure_ascii=False)
        return mark_safe(json_str)
    except Exception as e:
        # If JSON serialization fails, return a safe fallback
        return mark_safe('null')

@register.filter
def safe_json_with_fallback(value, fallback='null'):
    """
    Safely serialize a value to JSON with a custom fallback value.
    """
    try:
        if value is None:
            return mark_safe(fallback)
        return safe_json(value)
    except:
        return mark_safe(fallback)

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Replace or add URL parameters while preserving existing ones."""
    request = context['request']
    query_dict = request.GET.copy()
    
    for key, value in kwargs.items():
        if value is None:
            query_dict.pop(key, None)
        else:
            query_dict[key] = value
    
    return '?' + urlencode(query_dict) 