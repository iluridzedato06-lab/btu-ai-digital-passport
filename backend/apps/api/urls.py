from django.urls import path

from . import views_admin as A
from . import views_auth as U
from . import views_public as P

urlpatterns = [
    path("health", P.health),
    path("public/issuer", P.issuer),
    path("public/stats", P.stats),
    path("public/catalog", P.catalog),
    path("public/verify/by-hash/<str:sha256>", P.verify_hash),
    path("public/verify/<str:code>", P.verify_code),
    path("auth/csrf", U.csrf),
    path("auth/magic-link/request", U.magic_link_request),
    path("auth/magic-link/consume", U.magic_link_consume),
    path("auth/logout", U.logout_view),
    path("me", U.me),
    path("me/passport/versions/<int:number>/download", U.my_download),
    path("admin/overview", A.overview),
    path("admin/sync-runs", A.sync_runs),
    path("admin/sync-runs/<uuid:pk>", A.sync_run_detail),
    path("admin/sheet-rows", A.sheet_rows),
    path("admin/withdrawals", A.withdrawals),
    path("admin/awards/<str:award_id>/withdraw", A.withdraw),
    path("admin/awards/<str:award_id>/keep", A.keep_award),
    path("admin/students", A.students),
    path("admin/students/<uuid:pk>", A.student_detail),
    path("admin/students/<uuid:pk>/reissue", A.reissue),
    path("admin/versions/<uuid:pk>", A.version_detail),
    path("admin/versions/<uuid:pk>/download", A.version_download),
    path("admin/versions/<uuid:pk>/reanchor", A.reanchor),
    path("admin/versions/<uuid:pk>/revoke", A.revoke),
    path("admin/audit", A.audit_log),
    path("admin/catalog", A.admin_catalog),
]
