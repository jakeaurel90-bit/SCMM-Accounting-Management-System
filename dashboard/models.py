from django.conf import settings
from django.db import models
from django.utils import timezone


class Pastor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="pastor",
    )
    name = models.CharField(max_length=120)
    branch = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    messenger = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def initials(self):
        words = [w for w in self.name.replace("Rev.", "").replace("Pastor", "").split() if w]
        return "".join(w[0] for w in words[:2]).upper() or "?"


class SalaryPayment(models.Model):
    STATUS_CHOICES = [("Paid", "Paid"), ("Sent", "Sent")]

    pastor = models.ForeignKey(Pastor, related_name="salary_payments", on_delete=models.CASCADE)
    period_label = models.CharField(max_length=40, help_text="e.g. September 2026")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Paid")
    sent_on = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-sent_on"]

    def __str__(self):
        return f"{self.pastor} — {self.period_label}"


class BranchReportEntry(models.Model):
    pastor = models.ForeignKey(Pastor, related_name="branch_reports", on_delete=models.CASCADE)
    period_label = models.CharField(max_length=40)
    tithes_offerings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    branch_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    treasurer_note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pastor.branch} — {self.period_label}"

    @property
    def net(self):
        return self.tithes_offerings + self.special_contributions - self.branch_expenses


class BudgetItem(models.Model):
    ACCOUNT_CHOICES = [
        ("Missions & Outreach Fund", "Missions & Outreach Fund"),
        ("Evangelism Materials", "Evangelism Materials"),
        ("Program Logistics", "Program Logistics"),
        ("General Fund", "General Fund"),
    ]

    title = models.CharField("Description", max_length=200)
    description = models.CharField(max_length=300, blank=True, help_text="Optional extra detail line")
    account = models.CharField(max_length=60, choices=ACCOUNT_CHOICES, default=ACCOUNT_CHOICES[0][0])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    program_period = models.CharField(max_length=40, default="September 2026")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.title


class SentAllotment(models.Model):
    sent_at = models.DateTimeField(default=timezone.now)
    channels = models.CharField(max_length=100, blank=True)
    recipients = models.ManyToManyField(Pastor, related_name="sent_allotments", blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    program_period = models.CharField(max_length=40, default="September 2026")

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Sent {self.sent_at:%Y-%m-%d %H:%M}"


class OrgSettings(models.Model):
    """Singleton-style row (pk is always 1) holding site-wide display settings."""
    organization_name = models.CharField(max_length=150, default="Grace Fellowship")
    treasurer_title = models.CharField(max_length=150, default="Treasurer — Grace Fellowship HQ")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.organization_name
