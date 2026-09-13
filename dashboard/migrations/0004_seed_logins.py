from django.contrib.auth.hashers import make_password
from django.db import migrations

PASTOR_USERNAMES = {
    "Rev. Ramon Dizon": "ramon",
    "Pastor Marites Cruz": "marites",
    "Pastor Josel Santos": "josel",
    "Rev. Elena Aquino": "elena",
    "Pastor Benjie Lopez": "benjie",
}

PASTOR_DEMO_PASSWORD = "pastor123"
TREASURER_USERNAME = "treasurer"
TREASURER_DEMO_PASSWORD = "treasurer123"


def create_logins(apps, schema_editor):
    """
    Creates a login for every Pastor that exists at migrate-time, plus the
    treasurer account. Since pastors are no longer seeded (0002 leaves the
    Pastor table empty), this will only create the treasurer login unless
    pastors have already been added another way before this runs.
    """
    User = apps.get_model("auth", "User")
    Pastor = apps.get_model("dashboard", "Pastor")

    hashed_pastor_password = make_password(PASTOR_DEMO_PASSWORD)
    for pastor in Pastor.objects.all():
        username = PASTOR_USERNAMES.get(pastor.name, pastor.name.lower().replace(" ", "."))
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"password": hashed_pastor_password},
        )
        if pastor.user_id != user.id:
            pastor.user_id = user.id
            pastor.save(update_fields=["user"])

    if not User.objects.filter(username=TREASURER_USERNAME).exists():
        User.objects.create(
            username=TREASURER_USERNAME,
            password=make_password(TREASURER_DEMO_PASSWORD),
            is_staff=True,
        )


def remove_logins(apps, schema_editor):
    User = apps.get_model("auth", "User")
    usernames = list(PASTOR_USERNAMES.values()) + [TREASURER_USERNAME]
    User.objects.filter(username__in=usernames).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0003_pastor_user"),
    ]

    operations = [
        migrations.RunPython(create_logins, remove_logins),
    ]
