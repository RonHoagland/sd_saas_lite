"""User-facing views for the maintenance app — Assets list and detail.

Read-only starter scaffolding (Phase 3 adds create/edit, ValueList-backed
asset_type, audit trail per spec §22).
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from maintenance.models import Asset


@login_required(login_url='/')
def assets_list_view(request):
    assets = (
        Asset.objects
        .select_related('customer')
        .order_by('-created_on')
    )
    return render(request, 'assets/list.html', {
        'active_nav': 'assets',
        'section_title': 'Assets',
        'assets': assets,
    })


@login_required(login_url='/')
def asset_detail_view(request, pk):
    asset = get_object_or_404(
        Asset.objects.select_related('customer'),
        pk=pk,
    )
    return render(request, 'assets/detail.html', {
        'active_nav': 'assets',
        'section_title': asset.name,
        'asset': asset,
    })
