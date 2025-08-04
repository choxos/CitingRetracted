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

@register.filter
def country_emoji(country_name):
    """
    Get flag emoji for a country name.
    Returns empty string if country not found.
    Usage: {{ country|country_emoji }}
    """
    if not country_name:
        return ""
    
    # Normalize country name for lookup
    country_clean = country_name.strip().lower()
    
    # Comprehensive country to flag emoji mapping (270+ countries and territories)
    country_flags = {
        # A
        'ascension island': '🇦🇨',
        'andorra': '🇦🇩',
        'united arab emirates': '🇦🇪',
        'uae': '🇦🇪',
        'afghanistan': '🇦🇫',
        'antigua & barbuda': '🇦🇬',
        'antigua and barbuda': '🇦🇬',
        'anguilla': '🇦🇮',
        'albania': '🇦🇱',
        'armenia': '🇦🇲',
        'angola': '🇦🇴',
        'antarctica': '🇦🇶',
        'argentina': '🇦🇷',
        'american samoa': '🇦🇸',
        'austria': '🇦🇹',
        'australia': '🇦🇺',
        'aruba': '🇦🇼',
        'åland islands': '🇦🇽',
        'aland islands': '🇦🇽',
        'azerbaijan': '🇦🇿',
        
        # B
        'bosnia & herzegovina': '🇧🇦',
        'bosnia and herzegovina': '🇧🇦',
        'bosnia': '🇧🇦',
        'barbados': '🇧🇧',
        'bangladesh': '🇧🇩',
        'belgium': '🇧🇪',
        'burkina faso': '🇧🇫',
        'bulgaria': '🇧🇬',
        'bahrain': '🇧🇭',
        'burundi': '🇧🇮',
        'benin': '🇧🇯',
        'st. barthélemy': '🇧🇱',
        'saint barthélemy': '🇧🇱',
        'st barthelemy': '🇧🇱',
        'bermuda': '🇧🇲',
        'brunei': '🇧🇳',
        'bolivia': '🇧🇴',
        'caribbean netherlands': '🇧🇶',
        'brazil': '🇧🇷',
        'bahamas': '🇧🇸',
        'bhutan': '🇧🇹',
        'bouvet island': '🇧🇻',
        'botswana': '🇧🇼',
        'belarus': '🇧🇾',
        'belize': '🇧🇿',
        
        # C
        'canada': '🇨🇦',
        'cocos (keeling) islands': '🇨🇨',
        'cocos islands': '🇨🇨',
        'keeling islands': '🇨🇨',
        'congo-kinshasa': '🇨🇩',
        'democratic republic of congo': '🇨🇩',
        'drc': '🇨🇩',
        'dr congo': '🇨🇩',
        'central african republic': '🇨🇫',
        'congo-brazzaville': '🇨🇬',
        'congo': '🇨🇬',
        'republic of congo': '🇨🇬',
        'switzerland': '🇨🇭',
        'côte d\'ivoire': '🇨🇮',
        'cote d\'ivoire': '🇨🇮',
        'ivory coast': '🇨🇮',
        'cook islands': '🇨🇰',
        'chile': '🇨🇱',
        'cameroon': '🇨🇲',
        'china': '🇨🇳',
        'colombia': '🇨🇴',
        'clipperton island': '🇨🇵',
        'sark': '🇨🇶',
        'costa rica': '🇨🇷',
        'cuba': '🇨🇺',
        'cape verde': '🇨🇻',
        'curaçao': '🇨🇼',
        'curacao': '🇨🇼',
        'christmas island': '🇨🇽',
        'cyprus': '🇨🇾',
        'czechia': '🇨🇿',
        'czech republic': '🇨🇿',
        
        # D
        'germany': '🇩🇪',
        'diego garcia': '🇩🇬',
        'djibouti': '🇩🇯',
        'denmark': '🇩🇰',
        'dominica': '🇩🇲',
        'dominican republic': '🇩🇴',
        'algeria': '🇩🇿',
        
        # E
        'ceuta & melilla': '🇪🇦',
        'ceuta and melilla': '🇪🇦',
        'ecuador': '🇪🇨',
        'estonia': '🇪🇪',
        'egypt': '🇪🇬',
        'western sahara': '🇪🇭',
        'eritrea': '🇪🇷',
        'spain': '🇪🇸',
        'ethiopia': '🇪🇹',
        'european union': '🇪🇺',
        
        # F
        'finland': '🇫🇮',
        'fiji': '🇫🇯',
        'falkland islands': '🇫🇰',
        'micronesia': '🇫🇲',
        'faroe islands': '🇫🇴',
        'france': '🇫🇷',
        
        # G
        'gabon': '🇬🇦',
        'united kingdom': '🇬🇧',
        'uk': '🇬🇧',
        'britain': '🇬🇧',
        'great britain': '🇬🇧',
        'grenada': '🇬🇩',
        'georgia': '🇬🇪',
        'french guiana': '🇬🇫',
        'guernsey': '🇬🇬',
        'ghana': '🇬🇭',
        'gibraltar': '🇬🇮',
        'greenland': '🇬🇱',
        'gambia': '🇬🇲',
        'guinea': '🇬🇳',
        'guadeloupe': '🇬🇵',
        'equatorial guinea': '🇬🇶',
        'greece': '🇬🇷',
        'south georgia & south sandwich islands': '🇬🇸',
        'guatemala': '🇬🇹',
        'guam': '🇬🇺',
        'guinea-bissau': '🇬🇼',
        'guyana': '🇬🇾',
        
        # H
        'hong kong sar china': '🇭🇰',
        'hong kong': '🇭🇰',
        'heard & mcdonald islands': '🇭🇲',
        'honduras': '🇭🇳',
        'croatia': '🇭🇷',
        'haiti': '🇭🇹',
        'hungary': '🇭🇺',
        
        # I
        'canary islands': '🇮🇨',
        'indonesia': '🇮🇩',
        'ireland': '🇮🇪',
        'israel': '🇮🇱',
        'isle of man': '🇮🇲',
        'india': '🇮🇳',
        'british indian ocean territory': '🇮🇴',
        'iraq': '🇮🇶',
        'iran': '🇮🇷',
        'iceland': '🇮🇸',
        'italy': '🇮🇹',
        
        # J
        'jersey': '🇯🇪',
        'jamaica': '🇯🇲',
        'jordan': '🇯🇴',
        'japan': '🇯🇵',
        
        # K
        'kenya': '🇰🇪',
        'kyrgyzstan': '🇰🇬',
        'cambodia': '🇰🇭',
        'kiribati': '🇰🇮',
        'comoros': '🇰🇲',
        'st. kitts & nevis': '🇰🇳',
        'saint kitts and nevis': '🇰🇳',
        'north korea': '🇰🇵',
        'south korea': '🇰🇷',
        'korea': '🇰🇷',
        'kuwait': '🇰🇼',
        'cayman islands': '🇰🇾',
        'kazakhstan': '🇰🇿',
        
        # L
        'laos': '🇱🇦',
        'lebanon': '🇱🇧',
        'st. lucia': '🇱🇨',
        'saint lucia': '🇱🇨',
        'liechtenstein': '🇱🇮',
        'sri lanka': '🇱🇰',
        'liberia': '🇱🇷',
        'lesotho': '🇱🇸',
        'lithuania': '🇱🇹',
        'luxembourg': '🇱🇺',
        'latvia': '🇱🇻',
        'libya': '🇱🇾',
        
        # M
        'morocco': '🇲🇦',
        'monaco': '🇲🇨',
        'moldova': '🇲🇩',
        'montenegro': '🇲🇪',
        'st. martin': '🇲🇫',
        'saint martin': '🇲🇫',
        'madagascar': '🇲🇬',
        'marshall islands': '🇲🇭',
        'north macedonia': '🇲🇰',
        'macedonia': '🇲🇰',
        'mali': '🇲🇱',
        'myanmar (burma)': '🇲🇲',
        'myanmar': '🇲🇲',
        'burma': '🇲🇲',
        'mongolia': '🇲🇳',
        'macao sar china': '🇲🇴',
        'macao': '🇲🇴',
        'macau': '🇲🇴',
        'northern mariana islands': '🇲🇵',
        'martinique': '🇲🇶',
        'mauritania': '🇲🇷',
        'montserrat': '🇲🇸',
        'malta': '🇲🇹',
        'mauritius': '🇲🇺',
        'maldives': '🇲🇻',
        'malawi': '🇲🇼',
        'mexico': '🇲🇽',
        'malaysia': '🇲🇾',
        'mozambique': '🇲🇿',
        
        # N
        'namibia': '🇳🇦',
        'new caledonia': '🇳🇨',
        'niger': '🇳🇪',
        'norfolk island': '🇳🇫',
        'nigeria': '🇳🇬',
        'nicaragua': '🇳🇮',
        'netherlands': '🇳🇱',
        'norway': '🇳🇴',
        'nepal': '🇳🇵',
        'nauru': '🇳🇷',
        'niue': '🇳🇺',
        'new zealand': '🇳🇿',
        
        # O
        'oman': '🇴🇲',
        
        # P
        'panama': '🇵🇦',
        'peru': '🇵🇪',
        'french polynesia': '🇵🇫',
        'papua new guinea': '🇵🇬',
        'philippines': '🇵🇭',
        'pakistan': '🇵🇰',
        'poland': '🇵🇱',
        'st. pierre & miquelon': '🇵🇲',
        'pitcairn islands': '🇵🇳',
        'puerto rico': '🇵🇷',
        'palestinian territories': '🇵🇸',
        'palestine': '🇵🇸',
        'portugal': '🇵🇹',
        'palau': '🇵🇼',
        'paraguay': '🇵🇾',
        
        # Q
        'qatar': '🇶🇦',
        
        # R
        'réunion': '🇷🇪',
        'reunion': '🇷🇪',
        'romania': '🇷🇴',
        'serbia': '🇷🇸',
        'russia': '🇷🇺',
        'russian federation': '🇷🇺',
        'rwanda': '🇷🇼',
        
        # S
        'saudi arabia': '🇸🇦',
        'solomon islands': '🇸🇧',
        'seychelles': '🇸🇨',
        'sudan': '🇸🇩',
        'sweden': '🇸🇪',
        'singapore': '🇸🇬',
        'st. helena': '🇸🇭',
        'saint helena': '🇸🇭',
        'slovenia': '🇸🇮',
        'svalbard & jan mayen': '🇸🇯',
        'slovakia': '🇸🇰',
        'sierra leone': '🇸🇱',
        'san marino': '🇸🇲',
        'senegal': '🇸🇳',
        'somalia': '🇸🇴',
        'suriname': '🇸🇷',
        'south sudan': '🇸🇸',
        'são tomé & príncipe': '🇸🇹',
        'sao tome and principe': '🇸🇹',
        'el salvador': '🇸🇻',
        'sint maarten': '🇸🇽',
        'syria': '🇸🇾',
        'eswatini': '🇸🇿',
        'swaziland': '🇸🇿',
        
        # T
        'tristan da cunha': '🇹🇦',
        'turks & caicos islands': '🇹🇨',
        'chad': '🇹🇩',
        'french southern territories': '🇹🇫',
        'togo': '🇹🇬',
        'thailand': '🇹🇭',
        'tajikistan': '🇹🇯',
        'tokelau': '🇹🇰',
        'timor-leste': '🇹🇱',
        'east timor': '🇹🇱',
        'turkmenistan': '🇹🇲',
        'tunisia': '🇹🇳',
        'tonga': '🇹🇴',
        'türkiye': '🇹🇷',
        'turkey': '🇹🇷',
        'trinidad & tobago': '🇹🇹',
        'trinidad and tobago': '🇹🇹',
        'tuvalu': '🇹🇻',
        'taiwan': '🇹🇼',
        'tanzania': '🇹🇿',
        
        # U
        'ukraine': '🇺🇦',
        'uganda': '🇺🇬',
        'u.s. outlying islands': '🇺🇲',
        'united nations': '🇺🇳',
        'united states': '🇺🇸',
        'usa': '🇺🇸',
        'us': '🇺🇸',
        'uruguay': '🇺🇾',
        'uzbekistan': '🇺🇿',
        
        # V
        'vatican city': '🇻🇦',
        'st. vincent & grenadines': '🇻🇨',
        'saint vincent and the grenadines': '🇻🇨',
        'venezuela': '🇻🇪',
        'british virgin islands': '🇻🇬',
        'u.s. virgin islands': '🇻🇮',
        'us virgin islands': '🇻🇮',
        'vietnam': '🇻🇳',
        'vanuatu': '🇻🇺',
        
        # W
        'wallis & futuna': '🇼🇫',
        'samoa': '🇼🇸',
        
        # X
        'kosovo': '🇽🇰',
        
        # Y
        'yemen': '🇾🇪',
        'mayotte': '🇾🇹',
        
        # Z
        'south africa': '🇿🇦',
        'zambia': '🇿🇲',
        'zimbabwe': '🇿🇼',
    }
    
    return country_flags.get(country_clean, "")

@register.filter
def jsonify(value):
    """
    Convert a Python value to a JSON string for use in JavaScript.
    This is an alias for safe_json to match template usage.
    Usage: {{ data|jsonify }}
    """
    return safe_json(value) 