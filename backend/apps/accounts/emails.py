from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

SUBJECTS = {
    "login": {"en": "Your sign-in link — BTU AI Skills Passport",
              "ka": "შესვლის ბმული — BTU AI უნარების პასპორტი"},
    "updated": {"en": "Your AI Skills Passport was updated",
                "ka": "თქვენი AI უნარების პასპორტი განახლდა"},
}


def _send(kind: str, to: str, locale: str, ctx: dict):
    locale = locale if locale in ("en", "ka") else "ka"
    ctx = {**ctx, "locale": locale, "base": settings.PUBLIC_BASE_URL}
    text = render_to_string(f"email/{kind}.txt", ctx)
    html = render_to_string(f"email/{kind}.html", ctx)
    msg = EmailMultiAlternatives(SUBJECTS[kind][locale], text, settings.DEFAULT_FROM_EMAIL, [to])
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


def send_login_link(email: str, token: str, locale: str):
    link = f"{settings.PUBLIC_BASE_URL}/{locale}/auth/callback#token={token}"
    _send("login", email, locale, {"link": link, "ttl": settings.MAGIC_LINK_TTL_MINUTES})


def send_passport_updated(email: str, passport_id: str, version: int):
    _send("updated", email, "ka", {"passport_id": passport_id, "version": version})
