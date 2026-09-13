import io
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import TemplateView

from .forms import (
    BudgetItemEditForm,
    BudgetItemForm,
    OrgSettingsForm,
    PastorProfileForm,
    SalaryPaymentForm,
)
from .models import BranchReportEntry, BudgetItem, OrgSettings, Pastor, SalaryPayment, SentAllotment

CURRENT_PROGRAM_NAME = "Evangelistic Program"
CURRENT_PERIOD = "September 2026"


def get_current_pastor(request):
    """The Pastor profile linked to the logged-in user, if any."""
    return getattr(request.user, "pastor", None)


def pastor_required(view_func):
    """Requires login AND a linked Pastor profile."""
    @wraps(view_func)
    @login_required(login_url="dashboard:login")
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, "pastor"):
            messages.error(request, "Your account isn't linked to a pastor profile.")
            return redirect("dashboard:index")
        return view_func(request, *args, **kwargs)
    return wrapper


def finance_required(view_func):
    """Requires login AND staff (finance office) access."""
    @wraps(view_func)
    @login_required(login_url="dashboard:login")
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You need finance office access for that page.")
            return redirect("dashboard:index")
        return view_func(request, *args, **kwargs)
    return wrapper


class IndexView(TemplateView):
    template_name = "dashboard/index.html"


class LedgerLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_staff:
            return reverse("dashboard:finance_overview")
        if hasattr(user, "pastor"):
            return reverse("dashboard:pastor_dashboard")
        return reverse("dashboard:index")


class LedgerLogoutView(LogoutView):
    next_page = "dashboard:index"


# ---------------------------------------------------------------------------
# Pastor-facing pages
# ---------------------------------------------------------------------------

@pastor_required
def pastor_dashboard_view(request):
    pastor = get_current_pastor(request)
    salary_history = pastor.salary_payments.all()[:5]
    current_salary = salary_history[0] if salary_history else None
    branch_report = pastor.branch_reports.first()
    context = {
        "pastor": pastor,
        "period": CURRENT_PERIOD,
        "current_salary": current_salary,
        "salary_history": salary_history,
        "branch_report": branch_report,
    }
    return render(request, "dashboard/pastor_dashboard.html", context)


@pastor_required
def salary_history_view(request):
    pastor = get_current_pastor(request)
    return render(request, "dashboard/salary_history.html", {
        "pastor": pastor,
        "salary_history": pastor.salary_payments.all(),
    })


@pastor_required
def branch_reports_view(request):
    pastor = get_current_pastor(request)
    return render(request, "dashboard/branch_reports.html", {
        "pastor": pastor,
        "branch_reports": pastor.branch_reports.all(),
    })


@pastor_required
def profile_view(request):
    pastor = get_current_pastor(request)
    if request.method == "POST":
        form = PastorProfileForm(request.POST, instance=pastor)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("dashboard:profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PastorProfileForm(instance=pastor)
    return render(request, "dashboard/profile.html", {"pastor": pastor, "form": form})


@login_required(login_url="dashboard:login")
def download_salary_slip(request, pk):
    payment = get_object_or_404(SalaryPayment, pk=pk)
    is_owner = hasattr(request.user, "pastor") and request.user.pastor.pk == payment.pastor_id
    if not (request.user.is_staff or is_owner):
        messages.error(request, "You don't have access to that salary slip.")
        return redirect("dashboard:index")

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 18)
    p.drawString(1 * inch, height - 1 * inch, "Ledger — Salary Slip")

    p.setFont("Helvetica", 11)
    lines = [
        f"Pastor: {payment.pastor.name}",
        f"Branch: {payment.pastor.branch}",
        f"Period: {payment.period_label}",
        f"Status: {payment.status}",
        f"Amount: PHP {payment.amount:,.2f}",
        f"Sent on: {payment.sent_on:%b %d, %Y, %I:%M %p}",
    ]
    y = height - 1.6 * inch
    for line in lines:
        p.drawString(1 * inch, y, line)
        y -= 0.3 * inch

    p.setFont("Helvetica-Oblique", 9)
    p.drawString(1 * inch, 1 * inch, "Generated by Ledger — Church Finance Dashboard")

    p.showPage()
    p.save()
    buffer.seek(0)

    filename = f"salary-slip-{payment.pastor.name.replace(' ', '_')}-{payment.period_label.replace(' ', '_')}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)


# ---------------------------------------------------------------------------
# Finance office pages
# ---------------------------------------------------------------------------

@finance_required
def finance_overview_view(request):
    org = OrgSettings.load()
    context = {
        "org": org,
        "pastor_count": Pastor.objects.count(),
        "total_budget": BudgetItem.objects.aggregate(t=Sum("amount"))["t"] or 0,
        "total_salaries_paid": SalaryPayment.objects.filter(status="Paid").aggregate(t=Sum("amount"))["t"] or 0,
        "recent_sends": SentAllotment.objects.all()[:5],
    }
    return render(request, "dashboard/finance_overview.html", context)


@finance_required
def finance_dashboard_view(request):
    org = OrgSettings.load()
    budget_items = BudgetItem.objects.all()
    total_allotment = budget_items.aggregate(t=Sum("amount"))["t"] or 0
    recipients = Pastor.objects.all()
    context = {
        "org": org,
        "program_name": CURRENT_PROGRAM_NAME,
        "period": CURRENT_PERIOD,
        "budget_items": budget_items,
        "total_allotment": total_allotment,
        "recipients": recipients,
        "add_form": BudgetItemForm(),
    }
    return render(request, "dashboard/finance_dashboard.html", context)


@finance_required
def add_budget_item(request):
    if request.method == "POST":
        form = BudgetItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.program_period = CURRENT_PERIOD
            item.save()
            messages.success(request, "Budget line item added.")
        else:
            messages.error(request, "Couldn't add that line item — check the amount and description.")
    return redirect("dashboard:finance_dashboard")


@finance_required
def edit_budget_item(request, pk):
    item = get_object_or_404(BudgetItem, pk=pk)
    org = OrgSettings.load()
    if request.method == "POST":
        if "delete" in request.POST:
            item.delete()
            messages.success(request, "Line item removed.")
            return redirect("dashboard:finance_dashboard")
        form = BudgetItemEditForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Budget line item updated.")
            return redirect("dashboard:finance_dashboard")
        messages.error(request, "Please correct the errors below.")
    else:
        form = BudgetItemEditForm(instance=item)
    return render(request, "dashboard/edit_budget_item.html", {"form": form, "item": item, "org": org})


@finance_required
def send_allotment(request):
    if request.method == "POST":
        channels = request.POST.getlist("channels")
        recipient_ids = request.POST.getlist("recipients")
        recipients = Pastor.objects.filter(pk__in=recipient_ids)
        total = BudgetItem.objects.aggregate(t=Sum("amount"))["t"] or 0

        record = SentAllotment.objects.create(
            channels=", ".join(channels) if channels else "None selected",
            total_amount=total,
            program_period=CURRENT_PERIOD,
        )
        record.recipients.set(recipients)

        if recipients.exists():
            messages.success(
                request,
                f"Allotment sent to {recipients.count()} pastor(s) via {', '.join(channels) or 'no channel'}.",
            )
        else:
            messages.error(request, "Select at least one recipient before sending.")
    return redirect("dashboard:finance_dashboard")


@finance_required
def pastors_list_view(request):
    org = OrgSettings.load()
    if request.method == "POST":
        form = PastorProfileForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pastor added.")
            return redirect("dashboard:pastors_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PastorProfileForm()
    pastors = Pastor.objects.all()
    return render(request, "dashboard/pastors_list.html", {"pastors": pastors, "form": form, "org": org})


@finance_required
def edit_pastor(request, pk):
    pastor = get_object_or_404(Pastor, pk=pk)
    org = OrgSettings.load()
    if request.method == "POST":
        if "delete" in request.POST:
            name = pastor.name
            pastor.delete()
            messages.success(request, f"{name} was removed.")
            return redirect("dashboard:pastors_list")
        form = PastorProfileForm(request.POST, instance=pastor)
        if form.is_valid():
            form.save()
            messages.success(request, "Pastor updated.")
            return redirect("dashboard:pastors_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PastorProfileForm(instance=pastor)
    return render(request, "dashboard/edit_pastor.html", {"form": form, "pastor": pastor, "org": org})


@finance_required
def create_pastor_login(request, pk):
    pastor = get_object_or_404(Pastor, pk=pk)
    if pastor.user_id:
        messages.error(request, "This pastor already has a login.")
        return redirect("dashboard:edit_pastor", pk=pastor.pk)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        if not username or len(password) < 6:
            messages.error(request, "Enter a username and a password of at least 6 characters.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
        else:
            user = User.objects.create_user(username=username, password=password)
            pastor.user = user
            pastor.save(update_fields=["user"])
            messages.success(request, f"Login created for {pastor.name} — username: {username}.")
    return redirect("dashboard:edit_pastor", pk=pastor.pk)


@finance_required
def reset_pastor_password(request, pk):
    pastor = get_object_or_404(Pastor, pk=pk)
    if not pastor.user_id:
        messages.error(request, "This pastor doesn't have a login yet.")
        return redirect("dashboard:edit_pastor", pk=pastor.pk)

    if request.method == "POST":
        password = request.POST.get("password", "")
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            pastor.user.set_password(password)
            pastor.user.save()
            messages.success(request, f"Password reset for {pastor.name}.")
    return redirect("dashboard:edit_pastor", pk=pastor.pk)


@finance_required
def revoke_pastor_login(request, pk):
    pastor = get_object_or_404(Pastor, pk=pk)
    if request.method == "POST" and pastor.user_id:
        user = pastor.user
        pastor.user = None
        pastor.save(update_fields=["user"])
        user.delete()
        messages.success(request, f"Login revoked for {pastor.name}.")
    return redirect("dashboard:edit_pastor", pk=pastor.pk)


@finance_required
def salary_payments_view(request):
    org = OrgSettings.load()
    if request.method == "POST":
        form = SalaryPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Salary payment recorded.")
            return redirect("dashboard:salary_payments")
        messages.error(request, "Please correct the errors below.")
    else:
        form = SalaryPaymentForm(initial={"period_label": CURRENT_PERIOD, "status": "Paid"})
    payments = SalaryPayment.objects.select_related("pastor").all()
    return render(request, "dashboard/salary_payments.html", {"payments": payments, "form": form, "org": org})


@finance_required
def sent_history_view(request):
    org = OrgSettings.load()
    logs = SentAllotment.objects.prefetch_related("recipients").all()
    return render(request, "dashboard/sent_history.html", {"logs": logs, "org": org})


@finance_required
def settings_view(request):
    org = OrgSettings.load()
    if request.method == "POST":
        form = OrgSettingsForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings saved.")
            return redirect("dashboard:settings")
        messages.error(request, "Please correct the errors below.")
    else:
        form = OrgSettingsForm(instance=org)
    return render(request, "dashboard/settings.html", {"form": form, "org": org})
