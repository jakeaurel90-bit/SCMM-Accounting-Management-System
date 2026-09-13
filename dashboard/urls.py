from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("login/", views.LedgerLoginView.as_view(), name="login"),
    path("logout/", views.LedgerLogoutView.as_view(), name="logout"),

    # Pastor-facing
    path("pastor/", views.pastor_dashboard_view, name="pastor_dashboard"),
    path("pastor/salary-history/", views.salary_history_view, name="salary_history"),
    path("pastor/branch-reports/", views.branch_reports_view, name="branch_reports"),
    path("pastor/profile/", views.profile_view, name="profile"),
    path("pastor/salary/<int:pk>/slip.pdf", views.download_salary_slip, name="download_salary_slip"),

    # Finance office
    path("finance/overview/", views.finance_overview_view, name="finance_overview"),
    path("finance/", views.finance_dashboard_view, name="finance_dashboard"),
    path("finance/budget-items/add/", views.add_budget_item, name="add_budget_item"),
    path("finance/budget-items/<int:pk>/edit/", views.edit_budget_item, name="edit_budget_item"),
    path("finance/send-allotment/", views.send_allotment, name="send_allotment"),
    path("finance/pastors/", views.pastors_list_view, name="pastors_list"),
    path("finance/pastors/<int:pk>/edit/", views.edit_pastor, name="edit_pastor"),
    path("finance/pastors/<int:pk>/login/create/", views.create_pastor_login, name="create_pastor_login"),
    path("finance/pastors/<int:pk>/login/reset/", views.reset_pastor_password, name="reset_pastor_password"),
    path("finance/pastors/<int:pk>/login/revoke/", views.revoke_pastor_login, name="revoke_pastor_login"),
    path("finance/salary-payments/", views.salary_payments_view, name="salary_payments"),
    path("finance/sent-history/", views.sent_history_view, name="sent_history"),
    path("finance/settings/", views.settings_view, name="settings"),
]
