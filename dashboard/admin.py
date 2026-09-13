from django.contrib import admin

from .models import BranchReportEntry, BudgetItem, OrgSettings, Pastor, SalaryPayment, SentAllotment


@admin.register(Pastor)
class PastorAdmin(admin.ModelAdmin):
    list_display = ["name", "branch", "phone", "email"]
    search_fields = ["name", "branch"]


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ["pastor", "period_label", "amount", "status", "sent_on"]
    list_filter = ["status"]


@admin.register(BranchReportEntry)
class BranchReportEntryAdmin(admin.ModelAdmin):
    list_display = ["pastor", "period_label", "net"]


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ["title", "account", "amount", "program_period"]
    list_filter = ["account"]


@admin.register(SentAllotment)
class SentAllotmentAdmin(admin.ModelAdmin):
    list_display = ["sent_at", "channels", "total_amount", "program_period"]


@admin.register(OrgSettings)
class OrgSettingsAdmin(admin.ModelAdmin):
    list_display = ["organization_name", "treasurer_title"]
