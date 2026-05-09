# workforce/models.py
# Source: Data Models V6, Section 2.3.
#
# Models in this app:
#   WorkGroup, WorkGroupTeam, WGTRole, WGDivision, WorkGroupAsset,
#   Skill, EmployeeSkill
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from django.db import models
from config.base_models import TenantModel
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


class WGDivision(TenantModel, LifecycleMixin):
    """
    A named division that organises WorkGroups.
    Source: Data Models V6, Section 2.3.
    """
    lifecycle_entity_type = 'wg_division'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'workforce_wgdivision'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return self.name


class WorkGroup(TenantModel, NumberingMixin, LifecycleMixin):
    """
    A named work group (team / crew) within a division.
    Source: Data Models V6, Section 2.3.
    """
    numbering_entity_type = 'work_group'
    lifecycle_entity_type = 'work_group'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    work_group_number = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=200)
    division = models.ForeignKey(WGDivision, null=True, blank=True,
                                  on_delete=models.SET_NULL,
                                  related_name='work_groups')
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    description = models.TextField(blank=True)
    manager = models.ForeignKey('users.User', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='managed_work_groups')

    class Meta:
        db_table = 'workforce_workgroup'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'division_id']),
        ]

    def __str__(self):
        return self.name


class WGTRole(TenantModel):
    """
    A named role within a WorkGroup (e.g. Lead Technician, Helper).
    Source: Data Models V6, Section 2.3.
    """

    work_group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE,
                                    related_name='roles')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'workforce_wgtrole'
        indexes = [
            models.Index(fields=['tenant_id', 'work_group_id']),
        ]

    def __str__(self):
        return f'{self.work_group} — {self.name}'


class WorkGroupTeam(TenantModel):
    """
    A User's membership in a WorkGroup, with an optional role.
    Source: Data Models V6, Section 2.3.
    """

    work_group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE,
                                    related_name='team_members')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE,
                              related_name='work_group_memberships')
    role = models.ForeignKey(WGTRole, null=True, blank=True,
                              on_delete=models.SET_NULL,
                              related_name='members')
    is_lead = models.BooleanField(default=False)

    class Meta:
        db_table = 'workforce_workgroupteam'
        unique_together = [('work_group', 'user')]
        indexes = [
            models.Index(fields=['tenant_id', 'work_group_id']),
            models.Index(fields=['tenant_id', 'user_id']),
        ]

    def __str__(self):
        return f'{self.work_group} → {self.user}'


class WorkGroupAsset(TenantModel):
    """
    Asset assigned to / managed by a WorkGroup.
    Source: Data Models V6, Section 2.3.
    """

    work_group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE,
                                    related_name='assets')
    asset = models.ForeignKey('maintenance.Asset', on_delete=models.RESTRICT,
                               related_name='work_group_assignments')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'workforce_workgroupasset'
        unique_together = [('work_group', 'asset')]
        indexes = [
            models.Index(fields=['tenant_id', 'work_group_id']),
        ]

    def __str__(self):
        return f'{self.work_group} → {self.asset}'


# ─── Skills ───────────────────────────────────────────────────────────────────

class Skill(TenantModel):
    """
    Employee skill or certification definition.
    Source: Data Models V6, Section 3.3 (Pro/Enterprise).
    """

    class CategoryChoices(models.TextChoices):
        CERTIFICATION = 'Certification', 'Certification'
        LICENSE = 'License', 'License'
        TRAINING = 'Training', 'Training'
        COMPETENCY = 'Competency', 'Competency'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CategoryChoices.choices,
                                 default=CategoryChoices.COMPETENCY)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)

    class Meta:
        db_table = 'workforce_skill'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'category']),
        ]

    def __str__(self):
        return self.name


class EmployeeSkill(TenantModel):
    """
    Tracks a skill held by an employee with dates and status.
    Source: Data Models V6, Section 3.3 (Pro/Enterprise).
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        EXPIRED = 'Expired', 'Expired'

    employee = models.ForeignKey('users.User', on_delete=models.CASCADE,
                                  related_name='employee_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE,
                               related_name='employee_skills')
    date_earned = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)

    class Meta:
        db_table = 'workforce_employeeskill'
        unique_together = [('tenant_id', 'employee', 'skill')]
        indexes = [
            models.Index(fields=['tenant_id', 'employee_id']),
            models.Index(fields=['tenant_id', 'skill_id']),
        ]

    def __str__(self):
        return f'{self.employee} — {self.skill}'
