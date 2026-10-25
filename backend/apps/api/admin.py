from django.contrib import admin

from apps.audit.models import AuditLog
from apps.chain.models import AnchorTransaction, ChainDeployment
from apps.passports.models import Passport, PassportVersion, SkillAward, SkillCatalog
from apps.sheets.models import SyncRow, SyncRun
from apps.students.models import Student


class ReadOnly(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Student)
class StudentAdmin(ReadOnly):
    list_display = ("student_number", "first_name", "last_name", "email", "consent_given_at")
    search_fields = ("student_number", "first_name", "last_name", "email")


@admin.register(Passport)
class PassportAdmin(ReadOnly):
    list_display = ("passport_id", "holder_first_name", "holder_last_name", "first_issued_on", "latest_version_number")
    search_fields = ("passport_id", "holder_last_name")


@admin.register(PassportVersion)
class VersionAdmin(ReadOnly):
    list_display = ("passport", "version_number", "status", "trigger_reason", "issued_at", "revoked_at")
    list_filter = ("status", "trigger_reason")


@admin.register(SkillCatalog)
class CatalogAdmin(ReadOnly):
    list_display = ("skill_code", "name_en", "stamp_type", "is_active")


@admin.register(SkillAward)
class AwardAdmin(ReadOnly):
    list_display = ("award_id", "student", "skill", "date_earned", "withdrawn_at")


@admin.register(AnchorTransaction)
class AnchorAdmin(ReadOnly):
    list_display = ("version", "status", "tx_hash", "block_number", "attempts")


@admin.register(ChainDeployment)
class DeploymentAdmin(ReadOnly):
    list_display = ("chain_id", "contract_address", "issuer_address", "created_at")


@admin.register(SyncRun)
class SyncRunAdmin(ReadOnly):
    list_display = ("created_at", "status", "adapter", "triggered_by", "rows_seen", "rows_errors", "versions_issued")


@admin.register(SyncRow)
class SyncRowAdmin(ReadOnly):
    list_display = ("tab", "row_key", "last_row_number", "last_status", "last_message")
    list_filter = ("tab", "last_status")


@admin.register(AuditLog)
class AuditAdmin(ReadOnly):
    list_display = ("created_at", "actor", "action", "target_type", "target_id")
    list_filter = ("action",)
