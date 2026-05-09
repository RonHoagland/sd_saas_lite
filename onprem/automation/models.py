# automation/models.py
# Source: Data Models V6, Sections 3.1, 3.2, 3.3, 3.5, 3.6.
#
# Models in this app:
#   CommunicationTrigger, CommunicationTemplate, TriggerTemplate, TriggerLog,
#   SafetyForm, WorkFlow, WFStep, WFStepToDo, WFTool, WFInventory, WFSafetyForm,
#   WOSFAnswer, Equipment, CheckInOut, CreditCard, EmployeePurchase,
#   Portfolio, PortfolioProject, PortfolioMember, Sprint, SprintMember, SprintTask,
#   Milestone, MilestoneTask, TerritoryZone
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from django.db import models
from config.base_models import TenantModel
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


class CommunicationTrigger(TenantModel, LifecycleMixin):
    """
    A rule that fires when a named event occurs in the system.
    Source: Data Models V6, Section 3.6.
    """
    lifecycle_entity_type = 'communication_trigger'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    name = models.CharField(max_length=200)
    event_name = models.CharField(max_length=100,
                                   help_text='Internal event key, e.g. work_order.status_changed')
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    description = models.TextField(blank=True)
    conditions = models.JSONField(default=dict, blank=True,
                                   help_text='Optional filter conditions evaluated at trigger time.')

    class Meta:
        db_table = 'automation_communicationtrigger'
        indexes = [
            models.Index(fields=['tenant_id', 'event_name']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.name} ({self.event_name})'


class CommunicationTemplate(TenantModel, LifecycleMixin):
    """
    An email / SMS / push notification template with merge-field support.
    Source: Data Models V6, Section 3.6.
    """
    lifecycle_entity_type = 'communication_template'

    class ChannelChoices(models.TextChoices):
        EMAIL = 'Email', 'Email'
        SMS = 'SMS', 'SMS'
        PUSH = 'Push', 'Push'
        IN_APP = 'In-App', 'In-App'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    name = models.CharField(max_length=200)
    channel = models.CharField(max_length=10, choices=ChannelChoices.choices,
                                default=ChannelChoices.EMAIL)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    subject = models.CharField(max_length=300, blank=True,
                                help_text='Used for email; may include merge fields.')
    body = models.TextField(help_text='Template body; supports merge fields with {{field_name}} syntax.')
    from_name = models.CharField(max_length=100, blank=True)
    from_email = models.EmailField(blank=True)

    class Meta:
        db_table = 'automation_communicationtemplate'
        indexes = [
            models.Index(fields=['tenant_id', 'channel']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.name} ({self.channel})'


class TriggerTemplate(TenantModel):
    """
    Associates a CommunicationTrigger with a CommunicationTemplate.
    One trigger can fan out to multiple templates (e.g. email + SMS).
    Source: Data Models V6, Section 3.6.
    """

    trigger = models.ForeignKey(CommunicationTrigger, on_delete=models.CASCADE,
                                 related_name='trigger_templates')
    template = models.ForeignKey(CommunicationTemplate, on_delete=models.CASCADE,
                                  related_name='trigger_templates')
    delay_minutes = models.PositiveIntegerField(default=0,
                                                 help_text='Delay after trigger fires before sending.')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'automation_triggertemplate'
        unique_together = [('trigger', 'template')]
        indexes = [
            models.Index(fields=['tenant_id', 'trigger_id']),
        ]

    def __str__(self):
        return f'{self.trigger} → {self.template}'


class TriggerLog(TenantModel):
    """
    Audit log of every time a TriggerTemplate fired and was sent.
    Source: Data Models V6, Section 3.6.
    """

    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        SENT = 'Sent', 'Sent'
        FAILED = 'Failed', 'Failed'
        SKIPPED = 'Skipped', 'Skipped'

    trigger_template = models.ForeignKey(TriggerTemplate, null=True, blank=True,
                                          on_delete=models.SET_NULL,
                                          related_name='logs')
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.PENDING)
    recipient = models.CharField(max_length=300, blank=True,
                                  help_text='Email address, phone number, or user ID.')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    context_snapshot = models.JSONField(default=dict, blank=True,
                                         help_text='Merge-field values used at send time.')

    class Meta:
        db_table = 'automation_triggerlog'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'trigger_template_id']),
        ]

    def __str__(self):
        return f'{self.trigger_template} → {self.recipient} ({self.status})'


# ─── Pro/Enterprise Tier — Safety & Compliance ──────────────────────────────


class SafetyForm(TenantModel, LifecycleMixin):
    """
    A reusable safety checklist/form that can be assigned to workflows or work orders.
    Source: Data Models V6, Section 3.2.
    """
    lifecycle_entity_type = 'safety_form'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        DRAFT = 'Draft', 'Draft'

    form_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    form_definition = models.JSONField(default=dict, blank=True,
                                        help_text='Field definitions for the safety form.')
    required_before_work = models.BooleanField(default=False)

    class Meta:
        db_table = 'automation_safetyform'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return self.form_name


# ─── Pro/Enterprise Tier — WorkFlow Engine ──────────────────────────────────


class WorkFlow(TenantModel, NumberingMixin, LifecycleMixin):
    """
    A reusable workflow template that defines a sequence of steps, tools, and inventory.
    Source: Data Models V6, Section 3.1.
    """

    numbering_entity_type = 'workflow'
    lifecycle_entity_type = 'workflow'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        DRAFT = 'Draft', 'Draft'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    work_order_type = models.CharField(max_length=100, blank=True,
                                        help_text='Auto-apply trigger for work order type.')

    class Meta:
        db_table = 'automation_workflow'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return self.name


class WFStep(TenantModel):
    """
    A step within a workflow, including estimated duration and associated tools/inventory.
    Source: Data Models V6, Section 3.1.
    """

    workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, related_name='steps')
    step_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    estimated_duration = models.DurationField(null=True, blank=True)

    class Meta:
        db_table = 'automation_wfstep'
        indexes = [
            models.Index(fields=['tenant_id', 'workflow_id']),
        ]

    def __str__(self):
        return f'{self.workflow} — Step {self.sort_order}: {self.step_name}'


class WFStepToDo(TenantModel):
    """
    A to-do item or task within a workflow step.
    Source: Data Models V6, Section 3.1.
    """

    wf_step = models.ForeignKey(WFStep, on_delete=models.CASCADE, related_name='todos')
    label = models.CharField(max_length=300)
    sort_order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=False)

    class Meta:
        db_table = 'automation_wfsteptodo'
        indexes = [
            models.Index(fields=['tenant_id', 'wf_step_id']),
        ]

    def __str__(self):
        return self.label


class WFTool(TenantModel):
    """
    Equipment/tools required for a workflow.
    Source: Data Models V6, Section 3.1.
    """

    workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, related_name='tools')
    equipment = models.ForeignKey('automation.Equipment', on_delete=models.RESTRICT,
                                   related_name='workflow_usage')

    class Meta:
        db_table = 'automation_wftool'
        unique_together = [('tenant_id', 'workflow', 'equipment')]
        indexes = [
            models.Index(fields=['tenant_id', 'workflow_id']),
        ]

    def __str__(self):
        return f'{self.workflow} — {self.equipment}'


class WFInventory(TenantModel):
    """
    Inventory items required for a workflow.
    Source: Data Models V6, Section 3.1.
    """

    workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, related_name='inventory_items')
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                 related_name='workflow_usage')
    quantity_required = models.DecimalField(max_digits=12, decimal_places=2, default=1)

    class Meta:
        db_table = 'automation_wfinventory'
        unique_together = [('tenant_id', 'workflow', 'product')]
        indexes = [
            models.Index(fields=['tenant_id', 'workflow_id']),
        ]

    def __str__(self):
        return f'{self.quantity_required}x {self.product} for {self.workflow}'


class WFSafetyForm(TenantModel):
    """
    Safety forms required for a workflow.
    Source: Data Models V6, Section 3.1.
    """

    workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, related_name='safety_forms')
    safety_form = models.ForeignKey(SafetyForm, on_delete=models.CASCADE, related_name='workflow_usage')

    class Meta:
        db_table = 'automation_wfsafetyform'
        unique_together = [('tenant_id', 'workflow', 'safety_form')]
        indexes = [
            models.Index(fields=['tenant_id', 'workflow_id']),
        ]

    def __str__(self):
        return f'{self.workflow} — {self.safety_form}'


class WOSFAnswer(TenantModel):
    """
    Completed safety form responses linked to work orders.
    Source: Data Models V6, Section 3.2.
    """

    work_order = models.ForeignKey('service.WorkOrder', on_delete=models.CASCADE,
                                    related_name='safety_form_answers')
    employee = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='safety_form_answers')
    safety_form = models.ForeignKey(SafetyForm, on_delete=models.CASCADE, related_name='answers')
    answers = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'automation_wosfanswer'
        indexes = [
            models.Index(fields=['tenant_id', 'work_order_id']),
            models.Index(fields=['tenant_id', 'safety_form_id']),
        ]

    def __str__(self):
        return f'{self.safety_form} answer for {self.work_order}'


# ─── Pro/Enterprise Tier — Equipment & Purchases ──────────────────────────────


class Equipment(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Equipment/tools that can be checked out by employees or assigned to workflows.
    Source: Data Models V6, Section 3.3.
    """

    numbering_entity_type = 'equipment'
    lifecycle_entity_type = 'equipment'

    class CategoryChoices(models.TextChoices):
        POWER_TOOL = 'Power Tool', 'Power Tool'
        HAND_TOOL = 'Hand Tool', 'Hand Tool'
        DIAGNOSTIC = 'Diagnostic', 'Diagnostic'
        SAFETY = 'Safety', 'Safety'
        OTHER = 'Other', 'Other'

    class StatusChoices(models.TextChoices):
        AVAILABLE = 'Available', 'Available'
        CHECKED_OUT = 'Checked Out', 'Checked Out'
        IN_REPAIR = 'In Repair', 'In Repair'
        DECOMMISSIONED = 'Decommissioned', 'Decommissioned'

    equipment_number = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CategoryChoices.choices,
                                 default=CategoryChoices.OTHER)
    serial_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.AVAILABLE)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'automation_equipment'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'category']),
        ]

    def __str__(self):
        return f'[{self.equipment_number}] {self.name}'


class CheckInOut(TenantModel):
    """
    Log of equipment check-ins and check-outs.
    Source: Data Models V6, Section 3.3.
    """

    class ConditionOutChoices(models.TextChoices):
        GOOD = 'Good', 'Good'
        FAIR = 'Fair', 'Fair'
        NEEDS_REPAIR = 'Needs Repair', 'Needs Repair'

    class ConditionInChoices(models.TextChoices):
        GOOD = 'Good', 'Good'
        FAIR = 'Fair', 'Fair'
        DAMAGED = 'Damaged', 'Damaged'

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='check_in_outs')
    employee = models.ForeignKey('users.User', null=True, on_delete=models.SET_NULL,
                                  related_name='equipment_checkouts')
    checked_out_at = models.DateTimeField()
    checked_in_at = models.DateTimeField(null=True, blank=True,
                                          help_text='Null means equipment is still checked out.')
    condition_out = models.CharField(max_length=20, choices=ConditionOutChoices.choices,
                                      default=ConditionOutChoices.GOOD)
    condition_in = models.CharField(max_length=20, choices=ConditionInChoices.choices,
                                     blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'automation_checkinout'
        indexes = [
            models.Index(fields=['tenant_id', 'equipment_id']),
            models.Index(fields=['tenant_id', 'employee_id']),
        ]

    def __str__(self):
        return f'{self.equipment} → {self.employee} ({self.checked_out_at})'


class CreditCard(TenantModel):
    """
    Company credit card assigned to an employee for purchases.
    Source: Data Models V6, Section 3.3.
    """

    class CardTypeChoices(models.TextChoices):
        VISA = 'Visa', 'Visa'
        MASTERCARD = 'Mastercard', 'Mastercard'
        AMEX = 'Amex', 'Amex'
        OTHER = 'Other', 'Other'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        SUSPENDED = 'Suspended', 'Suspended'
        CANCELLED = 'Cancelled', 'Cancelled'

    employee = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='credit_cards')
    card_type = models.CharField(max_length=20, choices=CardTypeChoices.choices,
                                  default=CardTypeChoices.VISA)
    last_four = models.CharField(max_length=4)
    issuing_bank = models.CharField(max_length=100, blank=True)
    expiration_date = models.DateField()
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'automation_creditcard'
        indexes = [
            models.Index(fields=['tenant_id', 'employee_id']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.card_type} ****{self.last_four} ({self.employee})'


class EmployeePurchase(TenantModel):
    """
    Record of a purchase made by an employee, typically on a company credit card.
    Source: Data Models V6, Section 3.3.
    """

    class CategoryChoices(models.TextChoices):
        FUEL = 'Fuel', 'Fuel'
        PARTS = 'Parts', 'Parts'
        TOOLS = 'Tools', 'Tools'
        TRAVEL = 'Travel', 'Travel'
        OTHER = 'Other', 'Other'

    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'

    credit_card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='purchases')
    employee = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='purchases')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    purchase_date = models.DateField()
    description = models.CharField(max_length=300)
    category = models.CharField(max_length=20, choices=CategoryChoices.choices,
                                 default=CategoryChoices.OTHER)
    receipt_document = models.ForeignKey('documents.Document', null=True, blank=True,
                                          on_delete=models.SET_NULL, related_name='purchase_receipts')
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.PENDING)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'automation_employeepurchase'
        indexes = [
            models.Index(fields=['tenant_id', 'employee_id']),
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'credit_card_id']),
        ]

    def __str__(self):
        return f'{self.employee} — ${self.amount} ({self.purchase_date})'


# ─── Enterprise Tier — Project Management ────────────────────────────────────


class Portfolio(TenantModel):
    """
    A collection of projects grouped for strategic purposes.
    Source: Data Models V6, Section 3.5.
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        ARCHIVED = 'Archived', 'Archived'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)

    class Meta:
        db_table = 'automation_portfolio'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return self.name


class PortfolioProject(TenantModel):
    """
    Associates a WorkGroup project with a Portfolio.
    Source: Data Models V6, Section 3.5.
    """

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='projects')
    project = models.ForeignKey('workforce.WorkGroup', on_delete=models.CASCADE,
                                 related_name='portfolio_memberships')

    class Meta:
        db_table = 'automation_portfolioproject'
        unique_together = [('tenant_id', 'portfolio', 'project')]
        indexes = [
            models.Index(fields=['tenant_id', 'portfolio_id']),
        ]

    def __str__(self):
        return f'{self.portfolio} — {self.project}'


class PortfolioMember(TenantModel):
    """
    Associates an employee with a Portfolio.
    Source: Data Models V6, Section 3.5.
    """

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='members')
    employee = models.ForeignKey('users.User', on_delete=models.CASCADE,
                                  related_name='portfolio_memberships')

    class Meta:
        db_table = 'automation_portfoliomember'
        unique_together = [('tenant_id', 'portfolio', 'employee')]
        indexes = [
            models.Index(fields=['tenant_id', 'portfolio_id']),
        ]

    def __str__(self):
        return f'{self.portfolio} — {self.employee}'


class Sprint(TenantModel):
    """
    A time-boxed iteration within a project.
    Source: Data Models V6, Section 3.5.
    """

    class StatusChoices(models.TextChoices):
        PLANNED = 'Planned', 'Planned'
        ACTIVE = 'Active', 'Active'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'

    project = models.ForeignKey('workforce.WorkGroup', on_delete=models.CASCADE, related_name='sprints')
    name = models.CharField(max_length=200)
    goal = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.PLANNED)

    class Meta:
        db_table = 'automation_sprint'
        indexes = [
            models.Index(fields=['tenant_id', 'project_id']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.project} — {self.name}'


class SprintMember(TenantModel):
    """
    Associates an employee with a Sprint.
    Source: Data Models V6, Section 3.5.
    """

    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name='members')
    employee = models.ForeignKey('users.User', on_delete=models.CASCADE,
                                  related_name='sprint_memberships')

    class Meta:
        db_table = 'automation_sprintmember'
        unique_together = [('tenant_id', 'sprint', 'employee')]
        indexes = [
            models.Index(fields=['tenant_id', 'sprint_id']),
        ]

    def __str__(self):
        return f'{self.sprint} — {self.employee}'


class SprintTask(TenantModel):
    """
    Associates a Task with a Sprint.
    Source: Data Models V6, Section 3.5.
    """

    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name='tasks')
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, related_name='sprint_assignments')

    class Meta:
        db_table = 'automation_sprinttask'
        unique_together = [('tenant_id', 'sprint', 'task')]
        indexes = [
            models.Index(fields=['tenant_id', 'sprint_id']),
        ]

    def __str__(self):
        return f'{self.sprint} — {self.task}'


class Milestone(TenantModel):
    """
    A significant event or deadline within a project.
    Source: Data Models V6, Section 3.5.
    """

    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        IN_PROGRESS = 'In Progress', 'In Progress'
        COMPLETED = 'Completed', 'Completed'
        MISSED = 'Missed', 'Missed'

    project = models.ForeignKey('workforce.WorkGroup', on_delete=models.CASCADE,
                                 related_name='milestones')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.PENDING)

    class Meta:
        db_table = 'automation_milestone'
        indexes = [
            models.Index(fields=['tenant_id', 'project_id']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.project} — {self.name}'


class MilestoneTask(TenantModel):
    """
    Associates a Task with a Milestone.
    Source: Data Models V6, Section 3.5.
    """

    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='tasks')
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, related_name='milestone_assignments')

    class Meta:
        db_table = 'automation_milestonetask'
        unique_together = [('tenant_id', 'milestone', 'task')]
        indexes = [
            models.Index(fields=['tenant_id', 'milestone_id']),
        ]

    def __str__(self):
        return f'{self.milestone} — {self.task}'


# ─── Enterprise Tier — Territory Zones ───────────────────────────────────────


class TerritoryZone(TenantModel):
    """
    A geographic or organizational zone managed by an employee.
    Source: Data Models V6, Section 3.6.
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    name = models.CharField(max_length=200)
    employee = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='managed_zones', help_text='Zone manager.')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)

    class Meta:
        db_table = 'automation_territoryzone'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return self.name
