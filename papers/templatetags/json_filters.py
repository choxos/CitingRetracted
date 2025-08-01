import json
from datetime import date, datetime
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

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
        
        # Serialize to JSON with custom serializer
        json_str = json.dumps(value, default=json_serializer)
        return mark_safe(json_str)
        
    except (TypeError, ValueError) as e:
        # If serialization fails, provide a safe fallback
        if isinstance(value, list):
            return mark_safe('[]')
        elif isinstance(value, dict):
            return mark_safe('{}')
        else:
            return mark_safe('null')

@register.filter
def json_fallback(value, fallback='null'):
    """
    JSON filter with custom fallback value for failed serialization
    """
    try:
        if value is None:
            return mark_safe(fallback)
        return safe_json(value)
    except:
        return mark_safe(fallback) 