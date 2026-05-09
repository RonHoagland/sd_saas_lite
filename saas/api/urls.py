# api/urls.py
# Central URL configuration for the SDTA REST API.
# Source: Internal API Specification V1.
#
# All app routers are aggregated here under /api/v1/.
# Each app defines its own router in {app}/api.py.
#
# URL structure:
#   /api/v1/crm/customers/         → CRM customer list/create
#   /api/v1/crm/customers/{id}/    → CRM customer detail/update/delete
#   /api/v1/service/work-orders/   → Service work order list/create
#   /api/v1/numbering/rules/       → Numbering rule list/create
#   ... etc.

from django.urls import path, include
from api.auth import CSRFTokenView, SessionLoginView, SessionLogoutView, SessionMeView

from numbering.api import router as numbering_router
from lifecycle.api import router as lifecycle_router
from value_lists.api import router as value_lists_router
from notes.api import router as notes_router
from documents.api import router as documents_router
from crm.api import router as crm_router
from service.api import router as service_router
from maintenance.api import router as maintenance_router
from procurement.api import router as procurement_router
from tasks.api import router as tasks_router
from users.api import router as users_router
from workforce.api import router as workforce_router
from inventory.api import router as inventory_router
from warehouse.api import router as warehouse_router
from fleet.api import router as fleet_router
from automation.api import router as automation_router
from infrastructure.api import router as infrastructure_router


app_name = 'api'

urlpatterns = [
    # Auth/session bootstrap for frontend clients.
    path('auth/csrf/', CSRFTokenView.as_view(), name='auth-csrf'),
    path('auth/login/', SessionLoginView.as_view(), name='auth-login'),
    path('auth/logout/', SessionLogoutView.as_view(), name='auth-logout'),
    path('auth/me/', SessionMeView.as_view(), name='auth-me'),

    # Core framework APIs
    path('numbering/', include(numbering_router.urls)),
    path('lifecycle/', include(lifecycle_router.urls)),
    path('value-lists/', include(value_lists_router.urls)),
    path('notes/', include(notes_router.urls)),
    path('documents/', include(documents_router.urls)),

    # Domain APIs
    path('crm/', include(crm_router.urls)),
    path('service/', include(service_router.urls)),
    path('maintenance/', include(maintenance_router.urls)),
    path('procurement/', include(procurement_router.urls)),
    path('tasks/', include(tasks_router.urls)),
    path('users/', include(users_router.urls)),
    path('workforce/', include(workforce_router.urls)),
    path('inventory/', include(inventory_router.urls)),
    path('warehouse/', include(warehouse_router.urls)),
    path('fleet/', include(fleet_router.urls)),
    path('automation/', include(automation_router.urls)),
    path('infrastructure/', include(infrastructure_router.urls)),
]
