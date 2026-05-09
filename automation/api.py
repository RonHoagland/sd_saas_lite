# automation/api.py
# REST API serializers and viewsets for automation app models.
#
# Models (~25):
#   CommunicationTrigger, CommunicationTemplate, TriggerTemplate, TriggerLog,
#   SafetyForm, WorkFlow, WFStep, WFStepToDo, WFTool, WFInventory, WFSafetyForm,
#   WOSFAnswer, Equipment, CheckInOut, CreditCard, EmployeePurchase,
#   Portfolio, PortfolioProject, PortfolioMember, Sprint, SprintMember, SprintTask,
#   Milestone, MilestoneTask, TerritoryZone

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet, ReadOnlyTenantViewSet
from .models import (
    CommunicationTrigger, CommunicationTemplate, TriggerTemplate, TriggerLog,
    SafetyForm, WorkFlow, WFStep, WFStepToDo, WFTool, WFInventory, WFSafetyForm,
    WOSFAnswer, Equipment, CheckInOut, CreditCard, EmployeePurchase,
    Portfolio, PortfolioProject, PortfolioMember, Sprint, SprintMember, SprintTask,
    Milestone, MilestoneTask, TerritoryZone
)


# ─── Communication Triggers & Templates ────────────────────────────────────────

class CommunicationTriggerSerializer(TenantModelSerializer):

    class Meta:
        model = CommunicationTrigger
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'event_name',
            'status',
            'description',
            'conditions',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class CommunicationTriggerViewSet(TenantModelViewSet):
    queryset = CommunicationTrigger.objects.all()
    serializer_class = CommunicationTriggerSerializer
    filterset_fields = ['event_name', 'status']
    search_fields = ['name', 'event_name']
    ordering_fields = ['name', 'created_on', 'status']


class CommunicationTemplateSerializer(TenantModelSerializer):

    class Meta:
        model = CommunicationTemplate
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'channel',
            'status',
            'subject',
            'body',
            'from_name',
            'from_email',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class CommunicationTemplateViewSet(TenantModelViewSet):
    queryset = CommunicationTemplate.objects.all()
    serializer_class = CommunicationTemplateSerializer
    filterset_fields = ['channel', 'status']
    search_fields = ['name', 'subject']
    ordering_fields = ['name', 'channel', 'created_on', 'status']


class TriggerTemplateSerializer(TenantModelSerializer):
    trigger_display = serializers.CharField(source='trigger.name', read_only=True)
    template_display = serializers.CharField(source='template.name', read_only=True)

    class Meta:
        model = TriggerTemplate
        fields = TenantModelSerializer.Meta.fields + [
            'trigger',
            'trigger_display',
            'template',
            'template_display',
            'delay_minutes',
            'is_active',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'trigger_display',
            'template_display',
        ]


class TriggerTemplateViewSet(TenantModelViewSet):
    queryset = TriggerTemplate.objects.all()
    serializer_class = TriggerTemplateSerializer
    filterset_fields = ['trigger_id', 'template_id', 'is_active']
    search_fields = ['trigger__name', 'template__name']
    ordering_fields = ['created_on']


class TriggerLogSerializer(TenantModelSerializer):
    trigger_template_display = serializers.SerializerMethodField(read_only=True)

    def get_trigger_template_display(self, obj):
        return str(obj.trigger_template) if obj.trigger_template else None

    class Meta:
        model = TriggerLog
        fields = TenantModelSerializer.Meta.fields + [
            'trigger_template',
            'trigger_template_display',
            'status',
            'recipient',
            'sent_at',
            'error_message',
            'context_snapshot',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'trigger_template_display',
        ]


class TriggerLogViewSet(ReadOnlyTenantViewSet):
    queryset = TriggerLog.objects.all()
    serializer_class = TriggerLogSerializer
    filterset_fields = ['trigger_template_id', 'status']
    search_fields = ['recipient']
    ordering_fields = ['sent_at', 'created_on', 'status']


# ─── Safety Forms ────────────────────────────────────────────────────────────

class SafetyFormSerializer(TenantModelSerializer):

    class Meta:
        model = SafetyForm
        fields = TenantModelSerializer.Meta.fields + [
            'form_name',
            'description',
            'status',
            'form_definition',
            'required_before_work',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class SafetyFormViewSet(TenantModelViewSet):
    queryset = SafetyForm.objects.all()
    serializer_class = SafetyFormSerializer
    filterset_fields = ['status', 'required_before_work']
    search_fields = ['form_name']
    ordering_fields = ['form_name', 'created_on', 'status']


# ─── WorkFlow & Components ────────────────────────────────────────────────────

class WorkFlowSerializer(TenantModelSerializer):

    class Meta:
        model = WorkFlow
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'description',
            'status',
            'work_order_type',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class WorkFlowViewSet(TenantModelViewSet):
    queryset = WorkFlow.objects.all()
    serializer_class = WorkFlowSerializer
    filterset_fields = ['status']
    search_fields = ['name', 'work_order_type']
    ordering_fields = ['name', 'created_on', 'status']


class WFStepSerializer(TenantModelSerializer):
    workflow_display = serializers.CharField(source='workflow.name', read_only=True)

    class Meta:
        model = WFStep
        fields = TenantModelSerializer.Meta.fields + [
            'workflow',
            'workflow_display',
            'step_name',
            'description',
            'sort_order',
            'estimated_duration',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'workflow_display',
        ]


class WFStepViewSet(TenantModelViewSet):
    queryset = WFStep.objects.all()
    serializer_class = WFStepSerializer
    filterset_fields = ['workflow_id']
    search_fields = ['step_name', 'workflow__name']
    ordering_fields = ['sort_order', 'created_on']


class WFStepToDoSerializer(TenantModelSerializer):
    wf_step_display = serializers.SerializerMethodField(read_only=True)

    def get_wf_step_display(self, obj):
        return f"{obj.wf_step.workflow.name} — Step {obj.wf_step.sort_order}"

    class Meta:
        model = WFStepToDo
        fields = TenantModelSerializer.Meta.fields + [
            'wf_step',
            'wf_step_display',
            'label',
            'sort_order',
            'is_required',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'wf_step_display',
        ]


class WFStepToDoViewSet(TenantModelViewSet):
    queryset = WFStepToDo.objects.all()
    serializer_class = WFStepToDoSerializer
    filterset_fields = ['wf_step_id', 'is_required']
    search_fields = ['label']
    ordering_fields = ['sort_order', 'created_on']


class WFToolSerializer(TenantModelSerializer):
    workflow_display = serializers.CharField(source='workflow.name', read_only=True)
    equipment_display = serializers.CharField(source='equipment.name', read_only=True)

    class Meta:
        model = WFTool
        fields = TenantModelSerializer.Meta.fields + [
            'workflow',
            'workflow_display',
            'equipment',
            'equipment_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'workflow_display',
            'equipment_display',
        ]


class WFToolViewSet(TenantModelViewSet):
    queryset = WFTool.objects.all()
    serializer_class = WFToolSerializer
    filterset_fields = ['workflow_id', 'equipment_id']
    search_fields = ['workflow__name', 'equipment__name']
    ordering_fields = ['created_on']


class WFInventorySerializer(TenantModelSerializer):
    workflow_display = serializers.CharField(source='workflow.name', read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = WFInventory
        fields = TenantModelSerializer.Meta.fields + [
            'workflow',
            'workflow_display',
            'product',
            'product_display',
            'quantity_required',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'workflow_display',
            'product_display',
        ]


class WFInventoryViewSet(TenantModelViewSet):
    queryset = WFInventory.objects.all()
    serializer_class = WFInventorySerializer
    filterset_fields = ['workflow_id', 'product_id']
    search_fields = ['workflow__name', 'product__name']
    ordering_fields = ['created_on']


class WFSafetyFormSerializer(TenantModelSerializer):
    workflow_display = serializers.CharField(source='workflow.name', read_only=True)
    safety_form_display = serializers.CharField(source='safety_form.form_name', read_only=True)

    class Meta:
        model = WFSafetyForm
        fields = TenantModelSerializer.Meta.fields + [
            'workflow',
            'workflow_display',
            'safety_form',
            'safety_form_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'workflow_display',
            'safety_form_display',
        ]


class WFSafetyFormViewSet(TenantModelViewSet):
    queryset = WFSafetyForm.objects.all()
    serializer_class = WFSafetyFormSerializer
    filterset_fields = ['workflow_id', 'safety_form_id']
    search_fields = ['workflow__name', 'safety_form__form_name']
    ordering_fields = ['created_on']


class WOSFAnswerSerializer(TenantModelSerializer):
    work_order_display = serializers.SerializerMethodField(read_only=True)
    employee_display = serializers.CharField(source='employee.email', read_only=True)
    safety_form_display = serializers.CharField(source='safety_form.form_name', read_only=True)

    def get_work_order_display(self, obj):
        return str(obj.work_order_id)

    class Meta:
        model = WOSFAnswer
        fields = TenantModelSerializer.Meta.fields + [
            'work_order',
            'work_order_display',
            'employee',
            'employee_display',
            'safety_form',
            'safety_form_display',
            'answers',
            'completed_at',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'work_order_display',
            'employee_display',
            'safety_form_display',
        ]


class WOSFAnswerViewSet(TenantModelViewSet):
    queryset = WOSFAnswer.objects.all()
    serializer_class = WOSFAnswerSerializer
    filterset_fields = ['work_order_id', 'employee_id', 'safety_form_id']
    search_fields = []
    ordering_fields = ['completed_at', 'created_on']


# ─── Equipment & Purchases ────────────────────────────────────────────────────

class EquipmentSerializer(TenantModelSerializer):

    class Meta:
        model = Equipment
        fields = TenantModelSerializer.Meta.fields + [
            'equipment_number',
            'name',
            'category',
            'serial_number',
            'status',
            'purchase_date',
            'purchase_cost',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'equipment_number',
        ]


class EquipmentViewSet(TenantModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'equipment_number', 'serial_number']
    ordering_fields = ['name', 'created_on', 'status']


class CheckInOutSerializer(TenantModelSerializer):
    equipment_display = serializers.CharField(source='equipment.name', read_only=True)
    employee_display = serializers.CharField(source='employee.email', read_only=True)

    class Meta:
        model = CheckInOut
        fields = TenantModelSerializer.Meta.fields + [
            'equipment',
            'equipment_display',
            'employee',
            'employee_display',
            'checked_out_at',
            'checked_in_at',
            'condition_out',
            'condition_in',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'equipment_display',
            'employee_display',
        ]


class CheckInOutViewSet(TenantModelViewSet):
    queryset = CheckInOut.objects.all()
    serializer_class = CheckInOutSerializer
    filterset_fields = ['equipment_id', 'employee_id', 'condition_out', 'condition_in']
    search_fields = ['equipment__name', 'employee__email']
    ordering_fields = ['checked_out_at', 'checked_in_at', 'created_on']


class CreditCardSerializer(TenantModelSerializer):
    employee_display = serializers.CharField(source='employee.email', read_only=True)

    class Meta:
        model = CreditCard
        fields = TenantModelSerializer.Meta.fields + [
            'employee',
            'employee_display',
            'card_type',
            'last_four',
            'issuing_bank',
            'expiration_date',
            'credit_limit',
            'status',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'employee_display',
        ]


class CreditCardViewSet(TenantModelViewSet):
    queryset = CreditCard.objects.all()
    serializer_class = CreditCardSerializer
    filterset_fields = ['employee_id', 'card_type', 'status']
    search_fields = ['employee__email', 'last_four']
    ordering_fields = ['expiration_date', 'created_on', 'status']


class EmployeePurchaseSerializer(TenantModelSerializer):
    credit_card_display = serializers.SerializerMethodField(read_only=True)
    employee_display = serializers.CharField(source='employee.email', read_only=True)
    receipt_document_display = serializers.SerializerMethodField(read_only=True)

    def get_credit_card_display(self, obj):
        return f"{obj.credit_card.card_type} ****{obj.credit_card.last_four}"

    def get_receipt_document_display(self, obj):
        return str(obj.receipt_document_id) if obj.receipt_document else None

    class Meta:
        model = EmployeePurchase
        fields = TenantModelSerializer.Meta.fields + [
            'credit_card',
            'credit_card_display',
            'employee',
            'employee_display',
            'amount',
            'purchase_date',
            'description',
            'category',
            'receipt_document',
            'receipt_document_display',
            'status',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'credit_card_display',
            'employee_display',
            'receipt_document_display',
        ]


class EmployeePurchaseViewSet(TenantModelViewSet):
    queryset = EmployeePurchase.objects.all()
    serializer_class = EmployeePurchaseSerializer
    filterset_fields = ['credit_card_id', 'employee_id', 'category', 'status']
    search_fields = ['description', 'employee__email']
    ordering_fields = ['purchase_date', 'amount', 'created_on', 'status']


# ─── Portfolio & Project Management ────────────────────────────────────────────

class PortfolioSerializer(TenantModelSerializer):

    class Meta:
        model = Portfolio
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'description',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class PortfolioViewSet(TenantModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    filterset_fields = ['status']
    search_fields = ['name']
    ordering_fields = ['name', 'created_on', 'status']


class PortfolioProjectSerializer(TenantModelSerializer):
    portfolio_display = serializers.CharField(source='portfolio.name', read_only=True)
    project_display = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = PortfolioProject
        fields = TenantModelSerializer.Meta.fields + [
            'portfolio',
            'portfolio_display',
            'project',
            'project_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'portfolio_display',
            'project_display',
        ]


class PortfolioProjectViewSet(TenantModelViewSet):
    queryset = PortfolioProject.objects.all()
    serializer_class = PortfolioProjectSerializer
    filterset_fields = ['portfolio_id', 'project_id']
    search_fields = ['portfolio__name', 'project__name']
    ordering_fields = ['created_on']


class PortfolioMemberSerializer(TenantModelSerializer):
    portfolio_display = serializers.CharField(source='portfolio.name', read_only=True)
    employee_display = serializers.CharField(source='employee.email', read_only=True)

    class Meta:
        model = PortfolioMember
        fields = TenantModelSerializer.Meta.fields + [
            'portfolio',
            'portfolio_display',
            'employee',
            'employee_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'portfolio_display',
            'employee_display',
        ]


class PortfolioMemberViewSet(TenantModelViewSet):
    queryset = PortfolioMember.objects.all()
    serializer_class = PortfolioMemberSerializer
    filterset_fields = ['portfolio_id', 'employee_id']
    search_fields = ['portfolio__name', 'employee__email']
    ordering_fields = ['created_on']


class SprintSerializer(TenantModelSerializer):
    project_display = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Sprint
        fields = TenantModelSerializer.Meta.fields + [
            'project',
            'project_display',
            'name',
            'goal',
            'start_date',
            'end_date',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'project_display',
        ]


class SprintViewSet(TenantModelViewSet):
    queryset = Sprint.objects.all()
    serializer_class = SprintSerializer
    filterset_fields = ['project_id', 'status']
    search_fields = ['name', 'project__name']
    ordering_fields = ['start_date', 'end_date', 'created_on', 'status']


class SprintMemberSerializer(TenantModelSerializer):
    sprint_display = serializers.SerializerMethodField(read_only=True)
    employee_display = serializers.CharField(source='employee.email', read_only=True)

    def get_sprint_display(self, obj):
        return str(obj.sprint)

    class Meta:
        model = SprintMember
        fields = TenantModelSerializer.Meta.fields + [
            'sprint',
            'sprint_display',
            'employee',
            'employee_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'sprint_display',
            'employee_display',
        ]


class SprintMemberViewSet(TenantModelViewSet):
    queryset = SprintMember.objects.all()
    serializer_class = SprintMemberSerializer
    filterset_fields = ['sprint_id', 'employee_id']
    search_fields = ['sprint__name', 'employee__email']
    ordering_fields = ['created_on']


class SprintTaskSerializer(TenantModelSerializer):
    sprint_display = serializers.SerializerMethodField(read_only=True)
    task_display = serializers.CharField(source='task.title', read_only=True)

    def get_sprint_display(self, obj):
        return str(obj.sprint)

    class Meta:
        model = SprintTask
        fields = TenantModelSerializer.Meta.fields + [
            'sprint',
            'sprint_display',
            'task',
            'task_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'sprint_display',
            'task_display',
        ]


class SprintTaskViewSet(TenantModelViewSet):
    queryset = SprintTask.objects.all()
    serializer_class = SprintTaskSerializer
    filterset_fields = ['sprint_id', 'task_id']
    search_fields = ['sprint__name', 'task__title']
    ordering_fields = ['created_on']


class MilestoneSerializer(TenantModelSerializer):
    project_display = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Milestone
        fields = TenantModelSerializer.Meta.fields + [
            'project',
            'project_display',
            'name',
            'description',
            'due_date',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'project_display',
        ]


class MilestoneViewSet(TenantModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    filterset_fields = ['project_id', 'status']
    search_fields = ['name', 'project__name']
    ordering_fields = ['due_date', 'created_on', 'status']


class MilestoneTaskSerializer(TenantModelSerializer):
    milestone_display = serializers.SerializerMethodField(read_only=True)
    task_display = serializers.CharField(source='task.title', read_only=True)

    def get_milestone_display(self, obj):
        return str(obj.milestone)

    class Meta:
        model = MilestoneTask
        fields = TenantModelSerializer.Meta.fields + [
            'milestone',
            'milestone_display',
            'task',
            'task_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'milestone_display',
            'task_display',
        ]


class MilestoneTaskViewSet(TenantModelViewSet):
    queryset = MilestoneTask.objects.all()
    serializer_class = MilestoneTaskSerializer
    filterset_fields = ['milestone_id', 'task_id']
    search_fields = ['milestone__name', 'task__title']
    ordering_fields = ['created_on']


# ─── Territory Zones ──────────────────────────────────────────────────────────

class TerritoryZoneSerializer(TenantModelSerializer):
    employee_display = serializers.CharField(source='employee.email', read_only=True)

    class Meta:
        model = TerritoryZone
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'employee',
            'employee_display',
            'description',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'employee_display',
        ]


class TerritoryZoneViewSet(TenantModelViewSet):
    queryset = TerritoryZone.objects.all()
    serializer_class = TerritoryZoneSerializer
    filterset_fields = ['employee_id', 'status']
    search_fields = ['name']
    ordering_fields = ['name', 'created_on', 'status']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'communication-triggers', CommunicationTriggerViewSet, basename='communication-trigger')
router.register(r'communication-templates', CommunicationTemplateViewSet, basename='communication-template')
router.register(r'trigger-templates', TriggerTemplateViewSet, basename='trigger-template')
router.register(r'trigger-logs', TriggerLogViewSet, basename='trigger-log')
router.register(r'safety-forms', SafetyFormViewSet, basename='safety-form')
router.register(r'workflows', WorkFlowViewSet, basename='workflow')
router.register(r'wf-steps', WFStepViewSet, basename='wf-step')
router.register(r'wf-step-todos', WFStepToDoViewSet, basename='wf-step-todo')
router.register(r'wf-tools', WFToolViewSet, basename='wf-tool')
router.register(r'wf-inventory', WFInventoryViewSet, basename='wf-inventory')
router.register(r'wf-safety-forms', WFSafetyFormViewSet, basename='wf-safety-form')
router.register(r'wosf-answers', WOSFAnswerViewSet, basename='wosf-answer')
router.register(r'equipment', EquipmentViewSet, basename='equipment')
router.register(r'check-in-outs', CheckInOutViewSet, basename='check-in-out')
router.register(r'credit-cards', CreditCardViewSet, basename='credit-card')
router.register(r'employee-purchases', EmployeePurchaseViewSet, basename='employee-purchase')
router.register(r'portfolios', PortfolioViewSet, basename='portfolio')
router.register(r'portfolio-projects', PortfolioProjectViewSet, basename='portfolio-project')
router.register(r'portfolio-members', PortfolioMemberViewSet, basename='portfolio-member')
router.register(r'sprints', SprintViewSet, basename='sprint')
router.register(r'sprint-members', SprintMemberViewSet, basename='sprint-member')
router.register(r'sprint-tasks', SprintTaskViewSet, basename='sprint-task')
router.register(r'milestones', MilestoneViewSet, basename='milestone')
router.register(r'milestone-tasks', MilestoneTaskViewSet, basename='milestone-task')
router.register(r'territory-zones', TerritoryZoneViewSet, basename='territory-zone')
