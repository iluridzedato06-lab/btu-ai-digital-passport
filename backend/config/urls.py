from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "BTU AI Skills Passport — back office"
admin.site.site_title = "BTU AI Skills Passport"

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include("apps.api.urls")),
]
