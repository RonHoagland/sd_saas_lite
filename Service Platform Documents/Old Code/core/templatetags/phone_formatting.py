from django import template
from django.utils.safestring import mark_safe
import re
from core.models import Preference

register = template.Library()

@register.filter(name='phone_format')
def phone_format(value):
    """
    Formats a phone number according to the system preference 'loc_default_phone_format'.
    If the preference is not found, defaults to '(XXX) XXX-XXXX'.
    """
    if not value:
        return ""
        
    value = str(value)
    
    # 1. Get the mask from preferences
    try:
        mask_pref = Preference.objects.get(key='loc_default_phone_format')
        mask = mask_pref.value
    except Preference.DoesNotExist:
        mask = "(XXX) XXX-XXXX" # Fallback default
        
    # 2. Strip non-digit characters from the input value to get raw digits
    digits = re.sub(r'\D', '', value)
    
    # 3. Apply mask
    # Logic: iteratate through mask, replace 'X' with next digit.
    # If run out of digits, stop? Or leave Xs? 
    # Usually standard is fill as much as possible.
    
    formatted = ""
    digit_idx = 0
    
    for char in mask:
        if char == 'X':
            if digit_idx < len(digits):
                formatted += digits[digit_idx]
                digit_idx += 1
            else:
                # Ran out of digits but mask expects more. 
                # Behavior decision: incomplete mask? 
                # Let's break, treating rest as suffix if we want, or just stop.
                # If we stop, we might loose closing parenthesis.
                # Let's continue but maybe not replace? 
                # Simple approach: If no more digits, break logic might leave half-formatted string.
                # Better approach: If raw digits basically match length of Xs, it works.
                # If mismatched, maybe just return original?
                pass 
        else:
            formatted += char
            
    # Refined Logic:
    # If the number of digits doesn't roughly match the mask (e.g. 10 digits for US),
    # formatting might look weird.
    # Platform Core spec says: "All phone numbers should be set with the phone number mask"
    # Let's try to fill it.
    
    # Re-implementation for robustness:
    result = list(mask)
    digit_generator = (d for d in digits)
    
    try:
        for i, char in enumerate(result):
            if char == 'X':
                result[i] = next(digit_generator)
    except StopIteration:
        # We ran out of digits before filling the mask.
        # This implies the number is shorter than the mask.
        # E.g. Mask (XXX) XXX-XXXX, Value: 555-1234
        # Result so far: (555) 123-4XXX
        # We should probably strip remaining Xs or return original if it looks too broken.
        # For now, let's just return the original if it doesn't fit the mask reasonably well,
        # OR just strip the unfilled Xs.
        pass
        
    # Check if there are remaining 'X's in result?
    formatted_str = "".join(result)
    
    # If we still have Xs, it means we didn't have enough digits. 
    # Example: Mask requires 10, we have 7. Result: (555) 123-4XXX
    # This looks bad.
    if 'X' in formatted_str:
        # Fallback: Just return original value if it doesn't fit mask
        return value
        
    # If we have EXTRA digits leftovers?
    # next(digit_generator) might still have items.
    # If specific requirement says "Apply mask", we usually truncate or append.
    # Let's simply return formatted string.
    
    return formatted_str
