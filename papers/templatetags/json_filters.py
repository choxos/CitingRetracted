import json
from datetime import date, datetime
from django import template
from django.utils.safestring import mark_safe
from urllib.parse import urlencode
import math
import logging

logger = logging.getLogger(__name__)

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
def safe_floatformat(value, arg=None):
    """
    Safe version of floatformat that handles None, NaN, and infinity values.
    Usage: {{ value|safe_floatformat:2 }}
    """
    logger.debug(f"safe_floatformat called with value: {value}, arg: {arg}")
    try:
        # Handle None values
        if value is None:
            logger.debug("safe_floatformat: value is None, returning '0'")
            return "0"
        
        # Convert to float if it's not already
        if isinstance(value, str):
            value = float(value)
        
        # Handle NaN and infinity
        if math.isnan(value) or math.isinf(value):
            logger.debug(f"safe_floatformat: value is NaN or Inf ({value}), returning '0'")
            return "0"
        
        # Use Django's built-in floatformat for valid numbers
        from django.template.defaultfilters import floatformat
        result = floatformat(value, arg)
        logger.debug(f"safe_floatformat: successfully formatted {value} to {result}")
        return result
        
    except (ValueError, TypeError, OverflowError) as e:
        # Return "0" for any conversion errors
        logger.debug(f"safe_floatformat: error formatting {value}: {e}, returning '0'")
        return "0"

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