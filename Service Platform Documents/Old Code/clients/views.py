from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Client

@login_required
def client_list_view(request):
    """
    Display list of clients/customers.
    """
    # Sorting logic
    sort_by = request.GET.get('sort', 'name')
    direction = request.GET.get('direction', 'asc')
    
    # Map friendly URL names to model fields
    valid_sorts = {
        'account': 'account_number',
        'name': 'name',
        'status': 'status',
        'type': 'client_type',
        'date': 'date_started',
    }
    
    sort_field = valid_sorts.get(sort_by, 'name')
    
    # Toggle direction for next click
    order_prefix = '-' if direction == 'desc' else ''
    
    clients = Client.objects.all().order_by(f"{order_prefix}{sort_field}")
    
    context = {
        'clients': clients,
        'page_title': 'Client List',
        'current_sort': sort_by,
        'current_direction': direction
    }
    return render(request, "clients/client_list.html", context)
