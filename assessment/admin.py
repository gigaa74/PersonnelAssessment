from django.contrib import admin

from .models import Attempt, AuditEvent, CompetencyResult, Invitation, Response


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "bank_version", "created_at", "expires_at")
    list_filter = ("status", "bank_version")
    search_fields = ("email", "public_id")
    readonly_fields = ("public_id", "token_hash", "bank_version", "created_at", "sent_at", "completed_at")


admin.site.register(Attempt)
admin.site.register(Response)
admin.site.register(CompetencyResult)
admin.site.register(AuditEvent)
admin.site.site_header = "Оценка персонала"
admin.site.site_title = "Администрирование"

