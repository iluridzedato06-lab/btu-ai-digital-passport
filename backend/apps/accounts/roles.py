from django.conf import settings
from django.contrib.auth.models import Group

ADMIN = "admin"
STAFF = "staff"


def ensure_roles():
    for name in (ADMIN, STAFF):
        Group.objects.get_or_create(name=name)


def role_of(user) -> str:
    if not user or not user.is_authenticated:
        return "anon"
    names = set(user.groups.values_list("name", flat=True))
    if user.is_superuser or ADMIN in names:
        return "admin"
    if STAFF in names:
        return "staff"
    if hasattr(user, "student"):
        return "student"
    return "none"


def is_known_login(email: str) -> bool:
    from django.contrib.auth import get_user_model

    from apps.students.models import Student

    if email in settings.ADMIN_BOOTSTRAP_EMAILS:
        return True
    if Student.objects.filter(email=email).exists():
        return True
    User = get_user_model()
    return User.objects.filter(email=email, groups__name__in=[ADMIN, STAFF]).exists()


def sync_user_for_email(email: str):
    """Get or create the Django user for a verified email and attach roles / student record."""
    from django.contrib.auth import get_user_model

    from apps.students.models import Student

    ensure_roles()
    User = get_user_model()
    user = User.objects.filter(email=email).first()
    if user is None:
        user = User.objects.create(username=email[:150], email=email)
        user.set_unusable_password()
        user.save()
    if email in settings.ADMIN_BOOTSTRAP_EMAILS:
        user.groups.add(Group.objects.get(name=ADMIN))
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=["is_staff"])
    student = Student.objects.filter(email=email).first()
    if student and student.user_id != user.pk:
        student.user = user
        student.save(update_fields=["user", "updated_at"])
    return user
