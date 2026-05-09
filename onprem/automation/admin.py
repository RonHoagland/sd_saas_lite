# automation/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from automation.models import (
    CommunicationTrigger, CommunicationTemplate, TriggerTemplate, TriggerLog,
    SafetyForm, WorkFlow, WFStep, WFStepToDo, WFTool, WFInventory, WFSafetyForm,
    WOSFAnswer, Equipment, CheckInOut, CreditCard, EmployeePurchase,
    Portfolio, PortfolioProject, PortfolioMember, Sprint, SprintMember, SprintTask,
    Milestone, MilestoneTask, TerritoryZone,
)


@admin.register(CommunicationTrigger)
class CommunicationTriggerAdmin(TenantModelAdmin):
    list_display = ('name', 'event_name', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('name', 'event_name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(TenantModelAdmin):
    list_display = ('name', 'channel', 'status', 'subject', 'tenant_id')
    list_filter = ('tenant_id', 'channel', 'status')
    search_fields = ('name', 'subject')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(TriggerTemplate)
class TriggerTemplateAdmin(TenantModelAdmin):
    list_display = ('trigger', 'template', 'delay_minutes', 'is_active', 'tenant_id')
    list_filter = ('tenant_id', 'is_active')
    search_fields = ('trigger__name', 'template__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(TriggerLog)
class TriggerLogAdmin(TenantModelAdmin):
    list_display = ('trigger_template', 'recipient', 'status', 'sent_at', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('recipient',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on', 'context_snapshot')


@admin.register(SafetyForm)
class SafetyFormAdmin(TenantModelAdmin):
    list_display = ('form_name', 'status', 'required_before_work', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('form_name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WorkFlow)
class WorkFlowAdmin(TenantModelAdmin):
    list_display = ('name', 'status', 'work_order_type', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WFStep)
class WFStepAdmin(TenantModelAdmin):
    list_display = ('workflow', 'step_name', 'sort_order', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('workflow__name', 'step_name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WFStepToDo)
class WFStepToDoAdmin(TenantModelAdmin):
    list_display = ('wf_step', 'label', 'is_required', 'sort_order', 'tenant_id')
    list_filter = ('tenant_id', 'is_required')
    search_fields = ('wf_step__step_name', 'label')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WFTool)
class WFToolAdmin(TenantModelAdmin):
    list_display = ('workflow', 'equipment', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('workflow__name', 'equipment__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WFInventory)
class WFInventoryAdmin(TenantModelAdmin):
    list_display = ('workflow', 'product', 'quantity_required', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('workflow__name', 'product__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WFSafetyForm)
class WFSafetyFormAdmin(TenantModelAdmin):
    list_display = ('workflow', 'safety_form', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('workflow__name', 'safety_form__form_name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WOSFAnswer)
class WOSFAnswerAdmin(TenantModelAdmin):
    list_display = ('work_order', 'employee', 'safety_form', 'completed_at', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('work_order__id', 'employee__email', 'safety_form__form_name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Equipment)
class EquipmentAdmin(TenantModelAdmin):
    list_display = ('equipment_number', 'name', 'category', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'category')
    search_fields = ('equipment_number', 'name', 'serial_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(CheckInOut)
class CheckInOutAdmin(TenantModelAdmin):
    list_display = ('equipment', 'employee', 'checked_out_at', 'checked_in_at', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('equipment__name', 'employee__email')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(CreditCard)
class CreditCardAdmin(TenantModelAdmin):
    list_display = ('employee', 'card_type', 'last_four', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'card_type')
    search_fields = ('employee__email', 'last_four')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(EmployeePurchase)
class EmployeePurchaseAdmin(TenantModelAdmin):
    list_display = ('employee', 'amount', 'purchase_date', 'category', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'category')
    search_fields = ('employee__email', 'description')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Portfolio)
class PortfolioAdmin(TenantModelAdmin):
    list_display = ('name', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(TenantModelAdmin):
    list_display = ('portfolio', 'project', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('portfolio__name', 'project__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(PortfolioMember)
class PortfolioMemberAdmin(TenantModelAdmin):
    list_display = ('portfolio', 'employee', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('portfolio__name', 'employee__email')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Sprint)
class SprintAdmin(TenantModelAdmin):
    list_display = ('project', 'name', 'start_date', 'end_date', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('project__name', 'name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(SprintMember)
class SprintMemberAdmin(TenantModelAdmin):
    list_display = ('sprint', 'employee', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('sprint__name', 'employee__email')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(SprintTask)
class SprintTaskAdmin(TenantModelAdmin):
    list_display = ('sprint', 'task', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('sprint__name', 'task__id')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Milestone)
class MilestoneAdmin(TenantModelAdmin):
    list_display = ('project', 'name', 'due_date', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('project__name', 'name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(MilestoneTask)
class MilestoneTaskAdmin(TenantModelAdmin):
    list_display = ('milestone', 'task', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('milestone__name', 'task__id')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(TerritoryZone)
class TerritoryZoneAdmin(TenantModelAdmin):
    list_display = ('name', 'employee', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
