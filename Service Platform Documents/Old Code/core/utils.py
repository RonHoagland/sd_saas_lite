from django.db.models import QuerySet

def get_sort_params(request, default_sort: str = 'created', default_dir: str = 'desc'):
    """
    Extract sort parameters from request.
    Returns (sort_field, sort_direction)
    """
    sort_field = request.GET.get('sort', default_sort)
    sort_dir = request.GET.get('dir', default_dir)
    return sort_field, sort_dir

def apply_sorting(queryset: QuerySet, request, allowed_fields: list, default_sort: str = 'created', default_dir: str = 'desc'):
    """
    Apply sorting to a queryset based on request parameters.
    safely handling allowed fields.
    """
    sort_field, sort_dir = get_sort_params(request, default_sort, default_dir)
    
    if sort_field not in allowed_fields:
        sort_field = default_sort
        
    prefix = "-" if sort_dir == 'desc' else ""
    return queryset.order_by(f"{prefix}{sort_field}"), sort_field, sort_dir

import csv
from django.http import HttpResponse

def generate_csv_response(queryset, filename, field_mapping):
    """
    Generate a CSV response for a given queryset.
    
    Args:
        queryset: Django QuerySet to export
        filename: Output filename (e.g. 'users.csv')
        field_mapping: List of tuples [('Field Label', 'attribute_path')]
                       Attribute path can use dots for relationships (e.g. 'profile.phone_number')
                       
    Returns:
        HttpResponse with CSV content attached.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    
    # Write Header
    headers = [label for label, _ in field_mapping]
    writer.writerow(headers)

    # Write Data
    for obj in queryset:
        row = []
        for _, attr_path in field_mapping:
            # Resolve attribute path (e.g. "profile.phone_number")
            value = obj
            try:
                for part in attr_path.split('.'):
                    if value is None:
                        break
                    
                    if hasattr(value, part):
                         value = getattr(value, part)
                         # Handle methods/callables
                         if callable(value):
                             value = value()
                    elif isinstance(value, dict):
                         value = value.get(part)
                    else:
                         value = None
            except Exception:
                value = ""
                
            # Handle duplicates/lists if needed (basic string conversion)
            if value is None:
                value = ""
            row.append(str(value))
        writer.writerow(row)

    return response
