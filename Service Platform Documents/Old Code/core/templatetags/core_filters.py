from django import template
from core.models import Preference
import re

register = template.Library()

@register.filter(name='phone_format')
def phone_format(value):
    """
    Formats a phone number based on the system preference 'loc_default_phone_format'.
    If the value is empty or None, returns it as is.
    """
    if not value:
        return value

    try:
        # Get the format preference (cached ideally, but direct DB lookup for now)
        # Using .first() to avoid errors if missing, though we expect it to exist.
        pref = Preference.objects.filter(key='loc_default_phone_format').first()
        if not pref:
            return value # No mask defined, return raw
        
        mask = pref.value
        
        # Strip all non-digit characters from the input value
        digits = re.sub(r'\D', '', str(value))
        
        # Simple mask replacement: replace 'X' with digits
        # This is a basic implementation. 
        # For complex international handling, we might need a library like phonenumbers.
        # But this fulfills "use the phone number mask in preferences".
        
        result = ""
        digit_index = 0
        
        # Iterate through the mask and fill in digits
        for char in mask:
            if char == 'X':
                if digit_index < len(digits):
                    result += digits[digit_index]
                    digit_index += 1
                else:
                    # Ran out of digits? Stop or leave trailing format?
                    # Usually stop if we want flexible length, 
                    # or continue if we want to show strict partial mask.
                    # Let's stop to avoid weird half-empty masks.
                    break
            else:
                result += char
        
        # If we have extra digits that didn't fit in the mask (e.g. extension), append them?
        # Or just return the result?
        # Let's append them space-separated if there are leftovers, otherwise we lose data.
        if digit_index < len(digits):
            result += " " + digits[digit_index:]
            
        return result

    except Exception:
        # Fail safe to raw value on any error
        return value
