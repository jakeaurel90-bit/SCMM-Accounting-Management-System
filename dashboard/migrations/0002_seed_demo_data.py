from django.db import migrations


def seed_data(apps, schema_editor):
    BudgetItem = apps.get_model("dashboard", "BudgetItem")
    OrgSettings = apps.get_model("dashboard", "OrgSettings")

    # Pastors are intentionally NOT seeded — the finance office adds them
    # from the Pastors page (/finance/pastors/) once the app is running.

    if not BudgetItem.objects.exists():
        BudgetItem.objects.create(
            title="Outreach crusade — Kidapawan Plaza",
            description="3-day evangelistic campaign, Sep 20–22",
            account="Missions & Outreach Fund", amount="45000.00", program_period="September 2026",
        )
        BudgetItem.objects.create(
            title="Gospel tracts & printed materials",
            description="For house-to-house evangelism, all branches",
            account="Evangelism Materials", amount="8500.00", program_period="September 2026",
        )
        BudgetItem.objects.create(
            title="Sound system rental",
            description="For open-air evangelistic meeting",
            account="Program Logistics", amount="12000.00", program_period="September 2026",
        )

    OrgSettings.objects.get_or_create(
        pk=1, defaults={"organization_name": "Grace Fellowship", "treasurer_title": "Treasurer — Grace Fellowship HQ"},
    )


def unseed_data(apps, schema_editor):
    for name in ["BudgetItem", "OrgSettings"]:
        apps.get_model("dashboard", name).objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, unseed_data),
    ]
