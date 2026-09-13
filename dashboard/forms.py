from django import forms

from .models import BudgetItem, OrgSettings, Pastor, SalaryPayment


class BudgetItemForm(forms.ModelForm):
    """Used on the finance dashboard's 'New Line Item' card."""

    class Meta:
        model = BudgetItem
        fields = ["title", "account", "amount"]
        widgets = {
            "title": forms.Textarea(attrs={
                "placeholder": "e.g. Outreach crusade — Kidapawan Plaza",
                "rows": 3,
            }),
            "account": forms.Select(attrs={"class": "mono"}),
            "amount": forms.NumberInput(attrs={"class": "mono", "placeholder": "0.00", "step": "0.01"}),
        }


class BudgetItemEditForm(forms.ModelForm):
    """Used on the dedicated edit page — includes the extra detail line."""

    class Meta:
        model = BudgetItem
        fields = ["title", "description", "account", "amount"]
        widgets = {
            "title": forms.TextInput(),
            "description": forms.TextInput(attrs={"placeholder": "Optional extra detail line"}),
            "account": forms.Select(attrs={"class": "mono"}),
            "amount": forms.NumberInput(attrs={"class": "mono", "step": "0.01"}),
        }


class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ["pastor", "period_label", "amount", "status"]
        widgets = {
            "pastor": forms.Select(attrs={"class": "mono"}),
            "period_label": forms.TextInput(attrs={"placeholder": "e.g. October 2026"}),
            "amount": forms.NumberInput(attrs={"class": "mono", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "mono"}),
        }


class PastorProfileForm(forms.ModelForm):
    class Meta:
        model = Pastor
        fields = ["name", "branch", "phone", "email", "messenger"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "mono"}),
            "email": forms.EmailInput(attrs={"class": "mono"}),
            "messenger": forms.TextInput(attrs={"class": "mono", "placeholder": "m.me/username"}),
        }


class OrgSettingsForm(forms.ModelForm):
    class Meta:
        model = OrgSettings
        fields = ["organization_name", "treasurer_title"]
