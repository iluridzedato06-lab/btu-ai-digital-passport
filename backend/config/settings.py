"""Django settings for the BTU AI Skills Digital Passport.

All deployment-specific values come from environment variables (see ../.env.example).
"""
from pathlib import Path
import os

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return str(env(name, str(default))).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [x.strip() for x in str(env(name, default)).split(",") if x.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = env("SECRET_KEY") or ("dev-insecure-key-change-me" if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set when DJANGO_DEBUG is false")

PUBLIC_BASE_URL = env("PUBLIC_BASE_URL", "http://localhost:3000").rstrip("/")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,web,backend")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", PUBLIC_BASE_URL)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.core",
    "apps.audit",
    "apps.students",
    "apps.passports",
    "apps.chain",
    "apps.sheets",
    "apps.accounts",
    "apps.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = {
    "default": dj_database_url.parse(
        env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"), conn_max_age=60
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Tbilisi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/django-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = Path(env("MEDIA_ROOT", str(BASE_DIR / "media")))
MEDIA_URL = "/never-served-media/"  # PDFs are only served through authorised views

# --- Sessions / cookies -------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 12
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "btu_passport_session"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # the frontend reads it to send X-CSRFToken
CSRF_COOKIE_NAME = "csrftoken"
SECURE_COOKIES = env_bool("SECURE_COOKIES", not DEBUG and PUBLIC_BASE_URL.startswith("https"))
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
if env_bool("BEHIND_TLS_PROXY", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_REDIRECT_EXEMPT = [r"^api/health$"]

# --- REST framework ------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "verify": env("THROTTLE_VERIFY", "30/min"),
        "magic_link_ip": env("THROTTLE_MAGIC_LINK_IP", "10/hour"),
        "magic_link_email": env("THROTTLE_MAGIC_LINK_EMAIL", "3/15min"),
        "auth_consume": "20/hour",
        "admin_actions": "60/min",
    },
    "NUM_PROXIES": int(env("NUM_PROXIES", "1")),
    "EXCEPTION_HANDLER": "apps.api.exceptions.handler",
}

# --- Email ---------------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env("EMAIL_PORT", "1025"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "BTU AI Skills Passport <passport@btu.edu.ge>")

# --- Passport domain settings --------------------------------------------------
ALLOWED_EMAIL_DOMAINS = [d.lower() for d in env_list("ALLOWED_EMAIL_DOMAINS", "btu.edu.ge")]
ADMIN_BOOTSTRAP_EMAILS = [e.lower() for e in env_list("ADMIN_BOOTSTRAP_EMAILS", "")]
MAGIC_LINK_TTL_MINUTES = int(env("MAGIC_LINK_TTL_MINUTES", "15"))
VERIFY_LOCALE_IN_QR = env("VERIFY_LOCALE_IN_QR", "en")
ISSUER_NAME = "Business and Technology University"
ISSUER_NAME_KA = "ბიზნესისა და ტექნოლოგიების უნივერსიტეტი"
ISSUER_WEBSITE = "https://btu.edu.ge"

# Sheets
SHEETS_ADAPTER = env("SHEETS_ADAPTER", "local_xlsx")
LOCAL_SHEET_PATH = Path(env("LOCAL_SHEET_PATH", str(REPO_DIR / "data" / "local_sheet" / "passport_sheet.xlsx")))
SHEET_TEMPLATE_PATH = Path(
    env("SHEET_TEMPLATE_PATH", str(REPO_DIR / "data" / "sheet_template" / "BTU_AI_Passport_Sheet_Template.xlsx"))
)
SHOWCASE_DIR = Path(env("SHOWCASE_DIR", str(REPO_DIR / "data" / "showcase")))
GOOGLE_SPREADSHEET_ID = env("GOOGLE_SPREADSHEET_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON_B64 = env("GOOGLE_SERVICE_ACCOUNT_JSON_B64", "")
GOOGLE_SERVICE_ACCOUNT_FILE = env("GOOGLE_SERVICE_ACCOUNT_FILE", "")
SYNC_INTERVAL_SECONDS = int(env("SYNC_INTERVAL_SECONDS", "60"))
SYNC_AUTO_WITHDRAW = env_bool("SYNC_AUTO_WITHDRAW", False)

# Chain
CHAIN_RPC_URL = env("CHAIN_RPC_URL", "http://localhost:8545")
CHAIN_ID = int(env("CHAIN_ID", "31337"))
CHAIN_NAME = env("CHAIN_NAME", "Anvil (local development chain)")
CONTRACT_ADDRESS = env("CONTRACT_ADDRESS", "")
CHAIN_OWNER_PRIVATE_KEY = env("CHAIN_OWNER_PRIVATE_KEY", "")
CHAIN_ISSUER_PRIVATE_KEY = env("CHAIN_ISSUER_PRIVATE_KEY", "")
EXPLORER_TX_URL = env("EXPLORER_TX_URL", "")
EXPLORER_ADDRESS_URL = env("EXPLORER_ADDRESS_URL", "")
CHAIN_RECEIPT_TIMEOUT = int(env("CHAIN_RECEIPT_TIMEOUT", "120"))
MAX_ANCHOR_ATTEMPTS = int(env("MAX_ANCHOR_ATTEMPTS", "10"))
AUTO_DEPLOY_CONTRACT = env_bool("AUTO_DEPLOY_CONTRACT", False)
DEPLOYMENTS_DIR = Path(env("DEPLOYMENTS_DIR", str(REPO_DIR / "chain" / "deployments")))
CHAIN_ENABLED = env_bool("CHAIN_ENABLED", True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
    "loggers": {"fontTools": {"level": "WARNING"}, "weasyprint": {"level": "ERROR"}},
}
